
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
            tab_panels.append(f"<section class='tab-panel{active}' id='{slug}'>{html}</section>")

        body = f"""
<h1>Request On-Site Group Training</h1>
<p class='muted'>Tell us what your team needs, where you need it, and when you’d like it. We’ll use this request to match the right program, certifying body, and schedule.</p>

<div class='callout'>
  <strong>Transparent pricing matters.</strong>
  <p class='muted'>We show baseline pricing where it makes sense, then quote larger groups or unusual travel honestly instead of hiding everything behind “call for pricing.”</p>
</div>

<div data-tabs>
  <div class='tabs'>
    {''.join(tab_buttons)}
  </div>
  {''.join(tab_panels)}
</div>

<section class='section-box'>
  <h2>Tell us about your group</h2>
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
    <button class='button' type='submit'>Send Request</button>
  </form>
</section>
<script>
window.addEventListener('load', function () {{
  const params = new URLSearchParams(window.location.search);
  const requestedProgram = params.get('program');
  if (!requestedProgram) return;

  const target = Array.from(document.querySelectorAll('[data-program]')).find((button) => button.getAttribute('data-program') === requestedProgram);
  if (!target) return;

  const scope = target.closest('[data-tabs]');
  if (!scope) return;

  scope.querySelectorAll('.tab-btn').forEach((button) => button.classList.remove('active'));
  scope.querySelectorAll('.tab-panel').forEach((panel) => panel.classList.remove('active'));
  target.classList.add('active');

  const panel = scope.querySelector(target.getAttribute('data-tab-target'));
  if (panel) panel.classList.add('active');

  const input = document.querySelector('#program');
  if (input) input.value = requestedProgram;
}});
</script>
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
