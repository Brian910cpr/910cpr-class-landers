import { BLS, FAMILY, EVENT_SLUGS, CAPACITY, HOLD_MINUTES, COURSE_CENTS, EBOOK_CENTS, InputError, normalizeInput, fingerprint, uuidOk, checkoutMatches } from "./contract.ts";

const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization,x-client-info,apikey,content-type", "Access-Control-Allow-Methods": "GET,POST,OPTIONS" };
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {status, headers:{...cors,"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"}});
class ServiceError extends Error {
  status: number; code: string;
  constructor(message: string, status = 503, code = "temporarily_unavailable") { super(message); this.status = status; this.code = code; }
}
type Dependencies = { db: () => any; stripeKey: () => string | undefined; fetch: typeof fetch; now: () => number };

export function createHandler(deps: Dependencies) {
  return async (req: Request): Promise<Response> => {
    if (req.method === "OPTIONS") return new Response("ok", {headers: cors});
    if (!["GET", "POST"].includes(req.method)) return json({ok:false,error:"Method not allowed"},405);
    try {
      let body: any = {};
      if (req.method === "POST") {
        const raw = await req.text();
        if (raw.length > 16000) throw new InputError("The registration form is too large.");
        try { body = JSON.parse(raw); } catch { throw new InputError("Please submit a valid registration form."); }
        if (!body || typeof body !== "object" || Array.isArray(body)) throw new InputError("Invalid registration form.");
      }
      const url = new URL(req.url);
      const slug = url.searchParams.get("event") || body.event;
      if (!EVENT_SLUGS.includes(slug)) return json({ok:false,error:"Event not found"},404);
      const db = deps.db();
      const {data:sessions,error:se} = await db.from("class_sessions")
        .select("id,external_class_id,start_at,end_at,timezone,max_students,registration_backend,visibility,registration_status,price,registration_url,public_notes,course:courses!class_sessions_course_id_fkey(name,course_key,certifying_body),location:locations!class_sessions_location_id_fkey(name,address_line1,address_line2,city,state,postal_code),instructor:people!class_sessions_lead_instructor_id_fkey(display_name)")
        .in("external_class_id", EVENT_SLUGS);
      if (se) throw new ServiceError("Unable to load the event. Please try again.");
      const session = sessions?.find((s: any) => s.external_class_id === slug);
      if (!session) return json({ok:false,error:"Event not found"},404);
      const capacity = async () => {
        const {data,error} = await db.rpc("pool_event_capacity");
        if (error) throw new ServiceError("Unable to load availability. Please try again.");
        return {...data,handsOnCapacity:CAPACITY,capacityReason:"shared_manikin_pool",holdMinutes:HOLD_MINUTES};
      };
      const confirmedCapacity = async () => {
        try { return await capacity(); } catch { return {handsOnCapacity:CAPACITY,holdMinutes:HOLD_MINUTES,availabilityUnavailable:true}; }
      };
      if (req.method === "GET") return json({ok:true,event:{...session,...await capacity(),pricing:{currency:"usd",courseUnitCents:slug===BLS?COURSE_CENTS:0,ebookUnitCents:EBOOK_CENTS}}});
      if (body.company) return json({ok:false,error:"Unable to submit this registration."},400);
      const action = body.action ?? "submit";
      if (!["submit","status"].includes(action)) throw new InputError("Invalid registration action.");
      // Cached pre-rollout forms did not send requestId. Accept their initial
      // submit only; the atomic email guard prevents repeated registrations.
      if (action === "submit" && body.requestId === undefined) body.requestId = crypto.randomUUID();
      if (!uuidOk(body.requestId)) throw new InputError("Please reload the form before submitting.");
      const requestId = body.requestId.toLowerCase();
      const idempotencyKey = `pool2027:${slug}:${requestId}`;
      if (action === "submit") {
        if (session.registration_backend!=="landerware" || session.registration_status!=="open" || session.visibility!==(slug===FAMILY?"public":"unlisted") || new Date(session.start_at).getTime() <= deps.now()) throw new ServiceError("Registration is not open.",409,"registration_closed");
        const input = normalizeInput(body, slug);
        if (slug === BLS && !deps.stripeKey()) throw new ServiceError("Secure checkout is temporarily unavailable. Please try again.");
        const {data,error} = await db.rpc("reserve_pool_registration", {p_event:slug,p_request_id:requestId,p_fingerprint:await fingerprint(input,slug),p_input:input});
        if (error) throw new ServiceError("Unable to save registration. Retry with this same form.");
        if (!data?.ok) return json(data, data?.code === "invalid_input" ? 400 : 409);
      }
      const {data:registration,error:re} = await db.from("registrations").select("id,status,optional_survey,class_session_id").eq("idempotency_key",idempotencyKey).eq("class_session_id",session.id).maybeSingle();
      if (re) throw new ServiceError("Unable to check registration. Please try again.");
      if (!registration) return json({ok:false,error:"No registration was found for this attempt. Please submit the form.",code:"not_found"},404);
      const survey = registration.optional_survey;
      const common = {ok:true,requestId,registrationId:registration.id,groupRegistrationIds:survey.groupRegistrationIds,attendeeCount:survey.attendeeCount,ebookQty:survey.ebookQty??0};
      if (slug === FAMILY) return json({...common,confirmed:registration.status==="registered",event:await confirmedCapacity()});
      const {data:order,error:oe} = await db.from("registration_orders").select("id,status,total_amount,currency,stripe_checkout_session_id").eq("registration_id",registration.id).single();
      if (oe || !order) throw new ServiceError("Unable to check payment. Please retry this same registration.");
      if (body.checkoutSessionId && body.checkoutSessionId !== order.stripe_checkout_session_id) throw new ServiceError("That checkout does not match this registration.",409,"checkout_mismatch");
      if (order.status === "paid" && registration.status === "registered") return json({...common,confirmed:true,paymentPending:false,event:await confirmedCapacity()});
      if (order.status === "canceled") return json({...common,confirmed:false,paymentPending:false,expired:true,event:await confirmedCapacity()});
      if (!["payment_pending","payment_failed"].includes(order.status)) throw new ServiceError("This payment cannot be resumed. Please contact 910CPR.",409,"payment_unavailable");
      const key = deps.stripeKey();
      if (!key) throw new ServiceError("Secure checkout is temporarily unavailable. Please retry this same registration.");
      let checkout: any;
      if (order.stripe_checkout_session_id) {
        const response = await deps.fetch(`https://api.stripe.com/v1/checkout/sessions/${encodeURIComponent(order.stripe_checkout_session_id)}`, {headers:{authorization:`Bearer ${key}`},signal:AbortSignal.timeout(15000)});
        checkout = await response.json();
        if (!response.ok) throw new ServiceError("Unable to check secure checkout. Please try again.");
        if (!checkoutMatches(checkout,order,registration.id)) throw new ServiceError("Payment details could not be verified. Please contact 910CPR.",409,"payment_mismatch");
        if (checkout.payment_status === "paid") {
          const {data,error} = await db.rpc("confirm_pool_registration_payment", {p_registration_id:registration.id,p_checkout_session_id:checkout.id,p_amount_total:checkout.amount_total,p_currency:checkout.currency,p_payment_intent_id:typeof checkout.payment_intent==="string"?checkout.payment_intent:null});
          if (error || !data?.ok) throw new ServiceError("Payment received; confirmation is still processing. Please check again without paying again.");
          return json({...common,confirmed:true,paymentPending:false,event:await confirmedCapacity()});
        }
        if (checkout.status === "complete") return json({...common,confirmed:false,paymentPending:true,processing:true,event:await capacity()});
        if (checkout.status === "expired") {
          const {error} = await db.rpc("expire_pool_registration",{p_registration_id:registration.id,p_checkout_session_id:checkout.id});
          if (error) throw new ServiceError("Unable to release the expired checkout. Please retry this same registration.");
          return json({...common,confirmed:false,paymentPending:false,expired:true,event:await confirmedCapacity()});
        }
      } else {
        const expiresAt = Math.floor(new Date(survey.holdExpiresAt).getTime()/1000);
        if (!Number.isFinite(expiresAt)) throw new ServiceError("Unable to resume this registration. Please contact 910CPR.");
        // Replay the exact provider request even after a timeout. Stripe retains
        // idempotency results for 24h; outside that window require reconciliation.
        if (deps.now() > expiresAt*1000 + 22*60*60*1000) throw new ServiceError("Please contact 910CPR to reconcile this older checkout before registering again.",409,"payment_unavailable");
        const params = new URLSearchParams({mode:"payment",client_reference_id:registration.id,customer_email:survey.contactEmail,success_url:`https://www.910cpr.com/poolbls?session_id={CHECKOUT_SESSION_ID}&request_id=${requestId}`,cancel_url:`https://www.910cpr.com/poolbls?checkout_cancelled=1&request_id=${requestId}`,expires_at:String(expiresAt),"payment_method_types[0]":"card","metadata[pool_event]":slug,"metadata[order_id]":order.id,"metadata[registration_id]":registration.id});
        params.set("line_items[0][price_data][currency]","usd");
        params.set("line_items[0][price_data][unit_amount]",String(COURSE_CENTS));
        params.set("line_items[0][price_data][product_data][name]","AHA BLS Provider - February 15 community event");
        params.set("line_items[0][quantity]",String(survey.attendeeCount));
        if (survey.ebookQty > 0) {
          params.set("line_items[1][price_data][currency]","usd");
          params.set("line_items[1][price_data][unit_amount]",String(EBOOK_CENTS));
          params.set("line_items[1][price_data][product_data][name]","Optional 2025 AHA BLS Provider eManual");
          params.set("line_items[1][quantity]",String(survey.ebookQty));
        }
        const response = await deps.fetch("https://api.stripe.com/v1/checkout/sessions",{method:"POST",headers:{authorization:`Bearer ${key}`,"content-type":"application/x-www-form-urlencoded","idempotency-key":`pool2027-${requestId}`},body:params,signal:AbortSignal.timeout(15000)});
        checkout = await response.json();
        if (!response.ok && checkout.error?.type === "invalid_request_error" && checkout.error?.param === "expires_at") {
          if (expiresAt*1000 <= deps.now()) {
            // Replaying the same key found no successful Checkout Session. The
            // provider rejected its expired timestamp, so releasing is safe.
            const {error} = await db.rpc("expire_pool_registration",{p_registration_id:registration.id,p_checkout_session_id:null});
            if (error) throw new ServiceError("Unable to release this checkout. Please retry.");
            return json({...common,confirmed:false,paymentPending:false,expired:true,event:await confirmedCapacity()});
          }
          return json({...common,confirmed:false,paymentPending:true,checkoutUnavailable:true,holdExpiresAt:survey.holdExpiresAt,error:"Checkout could not start in time. Please try again after this hold expires.",event:await confirmedCapacity()});
        }
        if (!response.ok || !checkout.id) throw new ServiceError("Unable to start secure checkout. Retry with this same form; do not start another registration.");
        const {error} = await db.rpc("bind_pool_checkout",{p_registration_id:registration.id,p_request_id:requestId,p_checkout_session_id:checkout.id});
        if (error) throw new ServiceError("Checkout is being saved. Retry with this same form.");
        // A recovered cached session can already be paid/expired. Re-read it
        // through the same verification path rather than trust a stale redirect.
        if (checkout.status !== "open" || checkout.payment_status === "paid") {
          return createHandler(deps)(new Request(req.url,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({event:slug,action:"status",requestId})}));
        }
      }
      if (new Date(survey.holdExpiresAt).getTime() <= deps.now()) return json({...common,confirmed:false,paymentPending:true,processing:true,holdExpiresAt:survey.holdExpiresAt,event:await confirmedCapacity()});
      if (!checkout.url?.startsWith("https://checkout.stripe.com/")) throw new ServiceError("Secure checkout is temporarily unavailable.");
      return json({...common,confirmed:false,paymentPending:true,orderId:order.id,checkoutUrl:checkout.url,holdExpiresAt:survey.holdExpiresAt,event:await capacity()});
    } catch (error) {
      if (error instanceof InputError) return json({ok:false,error:error.message,code:"invalid_input"},400);
      if (error instanceof ServiceError) return json({ok:false,error:error.message,code:error.code},error.status);
      console.error("pool_registration_request_failed", error instanceof Error ? error.name : "UnknownError");
      return json({ok:false,error:"Something interrupted registration. Please retry with this same form.",code:"temporarily_unavailable"},503);
    }
  };
}
