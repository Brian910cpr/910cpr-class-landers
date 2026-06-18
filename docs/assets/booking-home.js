(function () {
  const sectionsRoot = document.querySelector("[data-home-sections]");
  if (!sectionsRoot) return;

  const PATHWAYS = [
    {
      id: "healthcare",
      title: "Healthcare Provider",
      audience: "For healthcare workers, nursing students, dental offices, hospital staff, EMS, and clinical requirements.",
      courses: ["BLS", "ACLS", "PALS"],
      formats: [
        { label: "BLS Provider / Renewal / HeartCode Skills", href: "/bls.html" },
        { label: "ACLS Provider / Renewal / HeartCode Skills", href: "/acls.html" },
        { label: "PALS Provider / Renewal / HeartCode Skills", href: "/pals.html" },
      ],
      primary: { label: "Start with BLS", href: "/bls.html" },
    },
    {
      id: "workplace",
      title: "Workplace, Daycare, School, or Coach",
      audience: "For workplace safety, childcare, schools, coaches, foster care, camps, and general CPR / first aid needs.",
      courses: ["Heartsaver First Aid CPR AED", "Heartsaver CPR AED", "Pediatric First Aid CPR AED", "Family & Friends CPR"],
      formats: [
        { label: "Heartsaver First Aid CPR AED", href: "/heartsaver.html" },
        { label: "Pediatric First Aid CPR AED", href: "/heartsaver.html?program=Pediatric%20First%20Aid%20CPR%20AED%20Blended" },
        { label: "Family & Friends / non-certification", href: "/heartsaver.html" },
      ],
      primary: { label: "Choose workplace or community class", href: "/heartsaver.html" },
    },
    {
      id: "arc",
      title: "American Red Cross Required",
      audience: "For students, employers, schools, or programs that specifically require Red Cross certification.",
      courses: ["ARC BLS", "ARC First Aid CPR AED", "ARC blended options where available"],
      formats: [
        { label: "Compare Red Cross options", href: "/arc.html" },
      ],
      primary: { label: "View Red Cross options", href: "/arc.html" },
    },
    {
      id: "hsi",
      title: "HSI Required",
      audience: "For employers, schools, or organizations that specifically accept or request HSI certification.",
      courses: ["HSI CPR AED", "HSI First Aid CPR AED", "HSI blended options where available"],
      formats: [
        { label: "Compare HSI options", href: "/hsi.html" },
      ],
      primary: { label: "View HSI options", href: "/hsi.html" },
    },
    {
      id: "uscg",
      title: "USCG / Maritime",
      audience: "For mariners, captains, crews, and maritime employers who need USCG-aligned first aid and CPR.",
      courses: ["USCG Elementary First Aid CPR AED"],
      formats: [
        { label: "USCG Elementary First Aid CPR AED", href: "/uscg-elementary-first-aid-cpr.html" },
      ],
      primary: { label: "View maritime options", href: "/uscg-elementary-first-aid-cpr.html" },
    },
    {
      id: "not-sure",
      title: "Not Sure What I Need",
      audience: "Use this path if your school, employer, licensing board, or agency gave you unclear course wording.",
      courses: ["Check the exact requirement before choosing a date"],
      formats: [
        { label: "Call 910-395-5193", href: "tel:9103955193" },
        { label: "Request group or help choosing", href: "/request_group_session.html" },
      ],
      primary: { label: "Get help choosing", href: "/request_group_session.html" },
    },
  ];

  function renderPathway(pathway) {
    const courseItems = pathway.courses.map((course) => `<li>${escapeHtml(course)}</li>`).join("");
    const formatLinks = pathway.formats
      .map((format) => `<a class="format-choice-link" href="${escapeAttribute(format.href)}">${escapeHtml(format.label)}</a>`)
      .join("");

    return `
      <article class="finder-card course-pathway-card" id="${escapeAttribute(pathway.id)}">
        <div class="finder-card-head">
          <div>
            <h3>${escapeHtml(pathway.title)}</h3>
            <p class="finder-card-copy">${escapeHtml(pathway.audience)}</p>
          </div>
          <a class="button secondary" href="${escapeAttribute(pathway.primary.href)}">${escapeHtml(pathway.primary.label)}</a>
        </div>
        <div class="course-pathway-body">
          <div>
            <strong>Common course names</strong>
            <ul class="course-pathway-list">${courseItems}</ul>
          </div>
          <div>
            <strong>Choose a delivery format or course page</strong>
            <div class="format-choice-list">${formatLinks}</div>
          </div>
        </div>
      </article>
    `;
  }

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

  sectionsRoot.innerHTML = PATHWAYS.map(renderPathway).join("");
})();
