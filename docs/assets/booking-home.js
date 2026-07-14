(function () {
  const sectionsRoot = document.querySelector("[data-home-sections]");
  if (!sectionsRoot) return;

  const COURSES = [
    {
      title: "AHA BLS",
      href: "/bls.html",
      image: "/images/bls_general.png",
    },
    {
      title: "AHA ACLS",
      href: "/acls.html",
      image: "/images/acls_general.png",
    },
    {
      title: "AHA PALS",
      href: "/pals.html",
      image: "/images/pals_general.png",
    },
    {
      title: "AHA Heartsaver First Aid CPR AED",
      href: "/heartsaver.html#first-aid-cpr-aed",
      image: "/images/heartsaver_general.png",
    },
    {
      title: "AHA Heartsaver CPR AED",
      href: "/heartsaver.html#cpr-aed",
      image: "/images/HS-FA-CPR-AED.jpeg",
    },
    {
      title: "ARC Programs",
      subtitle: "BLS and First Aid/CPR/AED",
      href: "/arc.html",
      image: "/images/0arc.png",
    },
    {
      title: "HSI Programs",
      subtitle: "BLS and First Aid/CPR/AED",
      href: "/hsi.html",
      image: "/images/0hsi.png",
    },
    {
      title: "USCG / Maritime",
      href: "/courses/uscg-first-aid-cpr-aed.html",
      image: "/images/maritime-first-aid.svg",
    },
    {
      title: "Family & Friends CPR",
      href: "/family-cpr.html",
      image: "/images/FF-CPR-2.jpg",
    },
  ];

  function renderCourseTile(course) {
    return `
      <a class="home-course-tile" href="${escapeAttribute(course.href)}">
        <img src="${escapeAttribute(course.image)}" alt="" loading="lazy" onerror="this.hidden=true">
        <span class="home-course-tile-copy">
          <strong>${escapeHtml(course.title)}</strong>
          ${course.subtitle ? `<span>${escapeHtml(course.subtitle)}</span>` : ""}
        </span>
      </a>
    `;
  }

  sectionsRoot.innerHTML = `
    <div class="home-course-grid" aria-label="Choose a course">
      ${COURSES.map(renderCourseTile).join("")}
    </div>
    <section class="home-help-panel" aria-label="Help choosing a class">
      <div>
        <h3>Need help choosing the right class?</h3>
        <p>Tell us what your employer, school, license, or personal goal requires, and we’ll point you to the right course.</p>
      </div>
      <div class="home-help-actions">
        <button class="button primary" type="button" data-course-chooser-toggle aria-expanded="false" aria-controls="guided-course-chooser">Help Me Choose the Right Class</button>
        <a class="button secondary" href="/group-training.html">Training for a group or workplace</a>
        <a class="button secondary" href="tel:9103955193">Call 910-395-5193</a>
      </div>
      <div class="home-course-chooser" id="guided-course-chooser" hidden tabindex="-1">
        <div class="home-course-chooser-grid">
          <section class="home-course-choice-group" aria-labelledby="chooser-healthcare">
            <h4 id="chooser-healthcare">Healthcare job or school</h4>
            <div class="home-choice-links">
              <a href="/bls.html">BLS</a>
              <a href="/acls.html">ACLS</a>
              <a href="/pals.html">PALS</a>
              <a href="/hsi.html#bls">HSI BLS</a>
            </div>
          </section>
          <section class="home-course-choice-group" aria-labelledby="chooser-workplace">
            <h4 id="chooser-workplace">Workplace, childcare, or safety requirement</h4>
            <div class="home-choice-links">
              <a href="/heartsaver.html#first-aid-cpr-aed">First Aid + CPR/AED</a>
              <a href="/heartsaver.html#cpr-aed">CPR/AED</a>
              <a href="/heartsaver.html#pediatric-first-aid-cpr-aed">Pediatric First Aid + CPR/AED</a>
            </div>
          </section>
          <section class="home-course-choice-group" aria-labelledby="chooser-family">
            <h4 id="chooser-family">Family or personal preparedness</h4>
            <div class="home-choice-links">
              <a href="/family-cpr.html">Family &amp; Friends CPR</a>
            </div>
          </section>
          <section class="home-course-choice-group" aria-labelledby="chooser-help">
            <h4 id="chooser-help">I still need help</h4>
            <div class="home-choice-links">
              <a href="tel:9103955193">Call 910CPR</a>
            </div>
          </section>
        </div>
        <section class="home-exact-wording" aria-labelledby="chooser-exact-wording">
          <h4 id="chooser-exact-wording">My employer or school gave me exact wording</h4>
          <label for="course-requirement-text">Paste the exact requirement here.</label>
          <textarea id="course-requirement-text" rows="3" data-course-requirement-text></textarea>
          <div class="home-help-secondary-actions">
            <button class="button secondary" type="button" data-copy-requirement-help>Copy help request</button>
            <a class="button secondary" data-context-email-link href="mailto:info@910cpr.com?subject=Help%20Choosing%20the%20Right%20CPR%20Class&amp;body=I%20need%20help%20choosing%20the%20correct%20class.%0D%0A%0D%0ARequirement%20from%20my%20employer%2C%20school%2C%20or%20license%3A%0D%0A%5Binsert%20text%5D%0D%0A%0D%0AMy%20deadline%3A%0D%0A%5Binsert%20date%5D">Email with this context</a>
          </div>
        </section>
      </div>
    </section>
  `;

  const chooserToggle = sectionsRoot.querySelector("[data-course-chooser-toggle]");
  const chooser = sectionsRoot.querySelector("#guided-course-chooser");
  const requirementText = sectionsRoot.querySelector("[data-course-requirement-text]");
  const copyHelpButton = sectionsRoot.querySelector("[data-copy-requirement-help]");
  const contextEmailLink = sectionsRoot.querySelector("[data-context-email-link]");

  function updateContextEmail() {
    if (!contextEmailLink) return;
    const requirement = requirementText?.value.trim() || "[insert text]";
    const body = [
      "I need help choosing the correct class.",
      "",
      "Requirement from my employer, school, or license:",
      requirement,
      "",
      "My deadline:",
      "[insert date]",
    ].join("\r\n");
    contextEmailLink.href = `mailto:info@910cpr.com?subject=${encodeURIComponent("Help Choosing the Right CPR Class")}&body=${encodeURIComponent(body)}`;
  }

  chooserToggle?.addEventListener("click", () => {
    if (!chooser || !chooserToggle) return;
    const expanded = chooserToggle.getAttribute("aria-expanded") === "true";
    chooser.hidden = expanded;
    chooserToggle.setAttribute("aria-expanded", String(!expanded));
    if (!expanded) {
      const firstLink = chooser.querySelector("a, button, textarea");
      (firstLink || chooser).focus();
    }
  });

  requirementText?.addEventListener("input", updateContextEmail);
  updateContextEmail();

  copyHelpButton?.addEventListener("click", async () => {
    const requirement = requirementText?.value.trim() || "[insert text]";
    const text = [
      "I need help choosing the correct class.",
      "",
      "Requirement from my employer, school, or license:",
      requirement,
      "",
      "My deadline:",
      "[insert date]",
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      copyHelpButton.textContent = "Copied";
    } catch (error) {
      copyHelpButton.textContent = "Copy this text manually";
      if (requirementText) requirementText.focus();
    }
  });

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value);
  }
})();
