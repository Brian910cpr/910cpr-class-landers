
from pathlib import Path
from scripts.build_status import BuildStatusReporter
from scripts.hub_utils import render_page

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "request_group_session.html"

TABS = [
    {
        "label": "BLS On-Site",
        "slug": "bls",
        "icon": "/images/25-bls-new.png",
        "icon_alt": "BLS on-site training",
        "panel_html": "<h2>BLS On-Site</h2><p>American Heart Association BLS Provider training delivered at your location. Ideal for healthcare offices, dental teams, clinics, and medical groups.</p><ul><li><strong>$700 for up to 12 participants</strong></li><li>We come to your location</li><li>Flexible scheduling</li><li>Approximately 2.5 hours</li></ul>",
    },
    {
        "label": "HeartCode BLS Group Skills",
        "slug": "heartcode",
        "icon": "/images/hc_b.png",
        "icon_alt": "HeartCode BLS skills testing",
        "panel_html": "<h2>HeartCode BLS Group Skills</h2><p>Blended package for offices that want online coursework plus a private on-site skills session.</p><ul><li><strong>$999 for up to 12 participants</strong></li><li>Includes HeartCode access and group skills testing</li><li>Completion certificates must be completed before the in-person session</li></ul>",
    },
    {
        "label": "First Aid / CPR / AED",
        "slug": "fa_cpr_aed",
        "icon": "/images/heartsaver_general.png",
        "icon_alt": "Heartsaver on-site training",
        "panel_html": "<h2>First Aid / CPR / AED</h2><p>Workplace-friendly group training for offices, schools, churches, and general workplace responders.</p><ul><li><strong>$400 + $35 per participant</strong> (up to 20)</li><li>Delivered at your location</li><li>Approximately 2.25 hours depending on program body</li></ul>",
    },
    {
        "label": "ACLS",
        "slug": "acls",
        "icon": "/images/25-acls-new.png",
        "icon_alt": "ACLS on-site training",
        "panel_html": "<h2>ACLS</h2><p>Advanced Cardiac Life Support group options for clinical teams. Best handled as a custom quote based on provider count, experience level, and desired format.</p>",
    },
    {
        "label": "PALS",
        "slug": "pals",
        "icon": "/images/25-pals-new.png",
        "icon_alt": "PALS on-site training",
        "panel_html": "<h2>PALS</h2><p>Pediatric Advanced Life Support group options for teams caring for infants and children. Custom scheduling available for appropriate groups.</p>",
    },
    {
        "label": "USCG Elementary First Aid | CPR",
        "slug": "uscg",
        "icon": "/images/stripes.png",
        "icon_alt": "USCG maritime training",
        "panel_html": "<h2>USCG Elementary First Aid | CPR</h2><p>Maritime-focused training options for teams needing USCG-aligned certification. Request details and preferred scheduling window below.</p>",
    },
]

def build():
    reporter = BuildStatusReporter("build_request_group_session")
    reporter.set_context(outputs=[OUTPUT])
    reporter.waiting(total=1)
    try:
        reporter.start(total=1)
        print("Building request group session page")
        tab_buttons = []
        tab_panels = []
        for i, tab in enumerate(TABS):
            active = " active" if i == 0 else ""
            label = tab["label"]
            slug = tab["slug"]
            icon = tab["icon"]
            icon_alt = tab["icon_alt"]
            html = tab["panel_html"]
            tab_buttons.append(
                f"<button class='tab-btn request-tab-btn{active}' data-program='{label}' data-tab-target='#{slug}' type='button'>"
                f"<img class='request-tab-image' src='{icon}' alt='{icon_alt}' loading='lazy' onerror=\"this.style.display='none'\">"
                f"<span class='request-tab-label'>{label}</span>"
                "</button>"
            )
            tab_panels.append(f"<section class='tab-panel{active}' id='{slug}'><div class='request-program-card'>{html}</div></section>")

        body = f"""
<div class='card request-shell'>
  <header class='site-brand-bar'>
    <a class='site-brand-link' href='/index.html' aria-label='910CPR home'><img class='site-brand-logo' src='/images/logo.png' alt='910CPR logo' onerror="this.src='/images/910CPR_wave.jpg';this.onerror=null;"><span class='site-brand-wordmark'>910CPR</span></a>
    <a class='site-header-phone' href='tel:+19103955193' aria-label='Call 910CPR at 910-395-5193'>910-395-5193</a>
  </header>
  <section class='hero request-hero'>
    <div class='hero-main'>
      <div class='eyebrow'>Private Team Training</div>
      <h1>Request On-Site Group Training</h1>
      <p class='subhead'>Tell us what your team needs, where you need it, and when you’d like it. We’ll help match the right training option and scheduling path for your group.</p>
      <div class='request-hero-actions'>
        <a class='button primary' href='#request-form'>Start your request</a>
        <a class='button secondary' href='/index.html'>Find an individual class</a>
      </div>
    </div>
    <div class='hero-side'>
      <div class='trust-badge request-hero-note'>
        <strong>Choose the training type below, then fill in the request form.</strong>
        <span>The tabs help prefill the right program so you do not have to guess which group option to ask for.</span>
      </div>
    </div>
  </section>

  <section class='section-box request-tabs-shell' id='request-programs' data-tabs data-sync-program='#program'>
    <div class='section-head'>
      <div class='section-title-wrap'>
        <h2>Choose the closest training format</h2>
        <p>Select the option that best matches your team so the form is prefilled with the right program name.</p>
      </div>
    </div>
    <div class='tabs hub-tabs request-tabs'>
      {''.join(tab_buttons)}
    </div>
    {''.join(tab_panels)}
  </section>

  <section class='request-form-grid'>
    <section class='section-box request-form-card' id='request-form'>
      <div class='request-form-head'>
        <div>
          <div class='eyebrow'>Request Details</div>
          <h2>Tell us about your group</h2>
        </div>
        <p class='muted'>Share the basics below and we’ll follow up with the best scheduling path for your team.</p>
      </div>
      <form method='post' action='#'>
        <input id='request_type' type='hidden' name='request_type' value='group'>
        <div class='grid-2'>
          <label class='field'><span>Name</span><input type='text' name='name' autocomplete='name' required></label>
          <label class='field'><span>Organization</span><input type='text' name='organization' autocomplete='organization'></label>
          <label class='field'><span>Email</span><input type='email' name='email' autocomplete='email' required></label>
          <label class='field'><span>Mobile</span><input type='tel' name='mobile' autocomplete='tel'></label>
          <label class='field'><span>City</span><input type='text' name='city' autocomplete='address-level2'></label>
          <label class='field'><span>On-site Address</span><input type='text' name='address' autocomplete='street-address'></label>
          <label class='field'><span>Estimated Headcount</span><input type='number' min='1' name='headcount'></label>
          <label class='field'><span>Desired Dates / Times</span><input type='text' name='preferred_times' placeholder='Any Thursday in May could work'></label>
        </div>
        <label class='field'><span>Program</span><input id='program' type='text' name='program' value='BLS On-Site'></label>
        <label class='field'><span>Comments / Special Requests</span>
          <textarea name='comments' placeholder='We have 12 for BLS, and 4 who need ACLS too.&#10;Any Thursday in May could work.&#10;Morning is better than afternoon.&#10;We may need training at our office in Morehead City.&#10;Some staff need Heartsaver, others need BLS.&#10;We already have AHA online completed, just need skills testing.'></textarea>
        </label>
        <div class='request-submit-row'>
          <button class='button primary' type='submit'>Send Request</button>
          <a class='button secondary' href='/index.html'>Compare individual seat options</a>
        </div>
      </form>
    </section>

    <aside class='section-box request-sidebar'>
      <div class='callout request-seat-board'>
        <strong>Need an individual seat schedule?</strong>
        <p class='muted'>If private group scheduling is not the right fit, use the public booking pages below to find the next available class.</p>
        <div class='request-link-list'>
          <a href='/bls.html'>Public BLS options</a>
          <a href='/heartsaver.html'>Public Heartsaver options</a>
          <a href='/acls.html'>Public ACLS options</a>
          <a href='/pals.html'>Public PALS options</a>
          <a href='/uscg-elementary-first-aid-cpr.html'>Public USCG options</a>
        </div>
      </div>
    </aside>
  </section>
</div>
<script>
(function () {{
  var params = new URLSearchParams(window.location.search);
  var program = (params.get("program") || "").trim();
  var requestType = (params.get("request_type") || "group").trim();
  var programInput = document.getElementById("program");
  var requestTypeInput = document.getElementById("request_type");
  if (requestTypeInput) requestTypeInput.value = requestType || "group";
  if (!program || !programInput) return;
  programInput.value = program;
  var normalizedProgram = program.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  var bestButton = null;
  document.querySelectorAll(".request-tab-btn[data-program]").forEach(function (button) {{
    var label = (button.getAttribute("data-program") || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
    if (!bestButton && (normalizedProgram.indexOf(label) !== -1 || label.indexOf(normalizedProgram) !== -1)) {{
      bestButton = button;
    }}
  }});
  if (!bestButton) {{
    if (normalizedProgram.indexOf("first aid") !== -1 || normalizedProgram.indexOf("cpr aed") !== -1) {{
      bestButton = document.querySelector(".request-tab-btn[data-tab-target='#fa_cpr_aed']");
    }} else if (normalizedProgram.indexOf("acls") !== -1) {{
      bestButton = document.querySelector(".request-tab-btn[data-tab-target='#acls']");
    }} else if (normalizedProgram.indexOf("pals") !== -1) {{
      bestButton = document.querySelector(".request-tab-btn[data-tab-target='#pals']");
    }} else if (normalizedProgram.indexOf("uscg") !== -1 || normalizedProgram.indexOf("maritime") !== -1) {{
      bestButton = document.querySelector(".request-tab-btn[data-tab-target='#uscg']");
    }} else if (normalizedProgram.indexOf("heartcode") !== -1) {{
      bestButton = document.querySelector(".request-tab-btn[data-tab-target='#heartcode']");
    }} else if (normalizedProgram.indexOf("bls") !== -1) {{
      bestButton = document.querySelector(".request-tab-btn[data-tab-target='#bls']");
    }}
  }}
  if (bestButton) bestButton.click();
}})();
</script>
"""
        html = render_page("Request On-Site Group Training | 910CPR", body, "Request on-site BLS, HeartCode BLS, First Aid/CPR/AED, ACLS, PALS, or USCG group training.")
        OUTPUT.write_text(html, encoding='utf-8')
        reporter.done(
            current=1,
            total=1,
            last_output_file=OUTPUT,
            pages_generated=1,
            counts={"request_tabs": len(TABS), "request_pages": 1},
        )
        print(f"Configured {len(TABS)} request tabs")
        print(f"Wrote {OUTPUT}")
    except Exception:
        reporter.error(last_output_file=OUTPUT if OUTPUT.exists() else None)
        raise

if __name__ == "__main__":
    build()
