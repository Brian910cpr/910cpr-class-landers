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
      href: "/courses/heartsaver-first-aid-cpr-aed.html",
      image: "/images/heartsaver_general.png",
    },
    {
      title: "AHA Heartsaver CPR AED",
      href: "/courses/heartsaver-cpr-aed.html",
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
      href: "/uscg-elementary-first-aid-cpr.html",
      image: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 160 120'%3E%3Crect width='160' height='120' rx='20' fill='%23e0f2fe'/%3E%3Cpath d='M18 82c17-8 31-8 48 0s31 8 48 0 29 8 46 0v38H18z' fill='%230f5e9c'/%3E%3Cpath d='M30 70h98l-14 22H45z' fill='%230f172a'/%3E%3Cpath d='M48 44h47l15 26H36z' fill='%23fff' stroke='%230f172a' stroke-width='4'/%3E%3Cpath d='M105 33h28v32h-28z' rx='5' fill='%23fff' stroke='%230f172a' stroke-width='4'/%3E%3Cpath d='M119 40v18M110 49h18' stroke='%23dc2626' stroke-width='6' stroke-linecap='round'/%3E%3C/svg%3E",
    },
    {
      title: "Family & Friends CPR",
      href: "/courses/aha-family-friends-cpr.html",
      image: "/images/confused-frustrated.png",
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
        <h3>Not sure which class you need?</h3>
        <p>Send us the wording from your job, school, email, or form. We'll help you avoid choosing the wrong class.</p>
      </div>
      <div class="home-help-actions">
        <a class="button primary" href="/index.html#class-finder">Help me choose</a>
        <a class="button secondary" href="/group-training.html">Training for a group or workplace</a>
        <a class="button secondary" href="tel:9103955193">Call 910-395-5193</a>
      </div>
    </section>
  `;

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
