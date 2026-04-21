
from pathlib import Path
from scripts.build_status import BuildStatusReporter
from scripts.hub_utils import render_page

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "request_group_session.html"

TABS = [
    ("BLS On-Site", "bls", "<h2>BLS On-Site</h2><p>American Heart Association BLS Provider training delivered at your location. Ideal for healthcare offices, dental teams, clinics, and medical groups.</p><ul><li><strong>$700 for up to 12 participants</strong></li><li>We come to your location</li><li>Flexible scheduling</li><li>Most classes run about 3.5 to 4 hours</li></ul>"),
    ("HeartCode BLS Group Skills", "heartcode", "<h2>HeartCode BLS Group Skills</h2><p>Blended package for offices that want online coursework plus a private on-site skills session.</p><ul><li><strong>$999 for up to 12 participants</strong></li><li>Includes HeartCode access and group skills testing</li><li>Completion certificates must be completed before the in-person session</li></ul>"),
    ("First Aid / CPR / AED", "fa_cpr_aed", "<h2>First Aid / CPR / AED</h2><p>Workplace-friendly group training for offices, schools, churches, and general workplace responders.</p><ul><li><strong>$400 + $35 per participant</strong> (up to 20)</li><li>Delivered at your location</li><li>Approx. 2.25 hours depending on program/body</li></ul>"),
    ("ACLS", "acls", "<h2>ACLS</h2><p>Advanced Cardiac Life Support group options for clinical teams. Best handled as a custom quote based on provider count, experience level, and desired format.</p>"),
    ("PALS", "pals", "<h2>PALS</h2><p>Pediatric Advanced Life Support group options for teams caring for infants and children. Custom scheduling available for appropriate groups.</p>"),
    ("USCG Elementary First Aid | CPR", "uscg", "<h2>USCG Elementary First Aid | CPR</h2><p>Maritime-focused training options for teams needing USCG-aligned certification. Request details and preferred scheduling window below.</p>"),
]

def build():
    reporter = BuildStatusReporter("build_request_group_session")
    reporter.waiting(total=1)
    try:
        reporter.start(total=1)
        print("Building request group session page")
        tab_buttons = []
        tab_panels = []
        for i, (label, slug, html) in enumerate(TABS):
            active = " active" if i == 0 else ""
            tab_buttons.append(f"<button class='tab-btn{active}' data-program='{label}' data-tab-target='#{slug}' type='button'>{label}</button>")
            tab_panels.append(f"<section class='tab-panel request-program-card{active}' id='{slug}'>{html}</section>")

        body = f"""
<div class='card request-shell'>
  <section class='hero request-hero'>
    <div class='hero-main'>
      <div class='eyebrow'>Private Team Training</div>
      <h1>Request On-Site Group Training</h1>
      <p class='subhead'>Pick the course path your team needs, then send one request with your location, headcount, and preferred dates. We’ll match the right format without making you decode internal schedule names.</p>
      <div class='slug-hero-actions'>
        <a class='button primary' href='#request-form'>Start Your Request</a>
        <a class='button secondary' href='/group-training.html'>See Group Training Overview</a>
      </div>
      <div class='slug-hero-picks'>
        <div class='slug-hero-picks-label'>Common Requests</div>
        <div class='request-badges'>
          <span class='badge'>Healthcare teams</span>
          <span class='badge'>Dental offices</span>
          <span class='badge'>Schools and churches</span>
          <span class='badge'>Maritime crews</span>
        </div>
      </div>
    </div>
    <div class='hero-side'>
      <div class='trust-badge'>
        <strong>Clear Pricing Where It Fits</strong>
        <span>Baseline group pricing stays visible when it makes sense, and custom quotes stay custom for larger or unusual requests.</span>
      </div>
      <div class='trust-badge'>
        <strong>One Form, Multiple Paths</strong>
        <span>Use the tabs below to compare BLS, HeartCode, Heartsaver, ACLS, PALS, and USCG options before you submit.</span>
      </div>
      <div class='slug-stat-grid request-stat-grid'>
        <div class='slug-stat'>
          <strong>6</strong>
          <span>program tracks</span>
        </div>
        <div class='slug-stat'>
          <strong>On-site</strong>
          <span>at your location</span>
        </div>
        <div class='slug-stat'>
          <strong>Fast</strong>
          <span>quote follow-up</span>
        </div>
      </div>
    </div>
  </section>

  <section class='section-box request-tabs-shell' data-tabs data-sync-program='#program'>
    <div class='tabs hub-tabs'>
      {''.join(tab_buttons)}
    </div>
    {''.join(tab_panels)}
  </section>

  <section class='request-form-grid' id='request-form'>
    <div class='section-box request-form-card'>
      <div class='request-form-head'>
        <div>
          <div class='slug-panel-kicker'>Step 2</div>
          <h2>Tell us about your team</h2>
          <p class='muted'>Share the basics and we’ll match the right training path, timing, and travel details.</p>
        </div>
      </div>
      <form method='post' action='#'>
        <div class='grid-2'>
          <label class='field'><span>Name</span><input type='text' name='name' required></label>
          <label class='field'><span>Organization</span><input type='text' name='organization'></label>
          <label class='field'><span>Email</span><input type='email' name='email' required></label>
          <label class='field'><span>Mobile</span><input type='tel' name='mobile'></label>
          <label class='field'><span>City</span><input type='text' name='city'></label>
          <label class='field'><span>On-site Address</span><input type='text' name='address'></label>
          <label class='field'><span>Estimated Headcount</span><input type='number' min='1' name='headcount'></label>
          <label class='field'><span>Desired Dates / Times</span><input type='text' name='preferred_times' placeholder='Any Thursday in May could work'></label>
        </div>
        <label class='field'><span>Program</span><input id='program' type='text' name='program' value='BLS On-Site'></label>
        <label class='field'><span>Comments / Special Requests</span>
          <textarea name='comments' placeholder='We have 12 for BLS, and 4 who need ACLS too.&#10;Any Thursday in May could work.&#10;Morning is better than afternoon.&#10;We may need training at our office in Morehead City.&#10;Some staff need Heartsaver, others need BLS.&#10;We already have AHA online completed, just need skills testing.'></textarea>
        </label>
        <p class='muted'>Current placeholder form only. Wire this to your preferred form handler or CRM next.</p>
        <button class='button primary' type='submit'>Send Request</button>
      </form>
    </div>

    <aside class='section-box request-sidebar'>
      <div class='slug-panel-kicker'>Before You Submit</div>
      <h2>What helps us quote faster</h2>
      <ul class='request-checklist'>
        <li>Approximate headcount and whether everyone needs the same certification</li>
        <li>Your city or full on-site address for travel planning</li>
        <li>Date windows that work best for your team</li>
        <li>Whether anyone already completed HeartCode online work</li>
      </ul>
      <div class='callout'>
        <strong>Need public seats instead?</strong>
        <p class='muted'>If you only need a few spots, the public class schedule may be faster than setting up a private session.</p>
      </div>
      <div class='request-link-list'>
        <a class='button secondary' href='/bls.html'>Browse BLS public dates</a>
        <a class='button secondary' href='/acls.html'>Browse ACLS public dates</a>
        <a class='button secondary' href='/heartsaver.html'>Browse Heartsaver public dates</a>
      </div>
    </aside>
  </section>
</div>
"""
        html = render_page("Request On-Site Group Training | 910CPR", body, "Request on-site BLS, HeartCode BLS, First Aid/CPR/AED, ACLS, PALS, or USCG group training.")
        OUTPUT.write_text(html, encoding='utf-8')
        reporter.done(current=1, total=1, last_output_file=OUTPUT)
        print(f"Configured {len(TABS)} request tabs")
        print(f"Wrote {OUTPUT}")
    except Exception:
        reporter.error(last_output_file=OUTPUT if OUTPUT.exists() else None)
        raise

if __name__ == "__main__":
    build()
