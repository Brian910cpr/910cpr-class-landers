# Public Site Semantic Route Pre-Commit Review

{
  "new_landers": 31,
  "new_failures": 0,
  "modified_counts": {
    "fragment-target-only": 0,
    "expected deterministic template change": 0,
    "schedule/content change": 94,
    "unexpected change": 0
  },
  "stale_cleanup": {
    "total_class_pages": 125,
    "public_schedule_class_ids": 125,
    "missing_public_linked_pages": [],
    "orphan_pages": [],
    "closed_full_pages": [],
    "private_pages": [],
    "past_pages": [],
    "duplicate_page_count": 0,
    "suppressed_ids_present": {
      "12774086": false,
      "12774096": false
    },
    "deleted_stale_pages": [
      "12774086",
      "12774096",
      "12774587",
      "12775320",
      "12776267"
    ]
  },
  "group_routes": [
    {
      "tab": "group-bls",
      "label": "Request on-site BLS group training",
      "href": "/request_group_session.html?program=BLS%20On-Site%20Group%20Training&request_type=group",
      "exists": true,
      "query": {
        "program": [
          "BLS On-Site Group Training"
        ],
        "request_type": [
          "group"
        ]
      },
      "advances": true,
      "individual_scheduler": false
    },
    {
      "tab": "group-heartsaver",
      "label": "Request First Aid / CPR / AED group training",
      "href": "/request_group_session.html?program=First%20Aid%20CPR%20AED%20Group%20Training&request_type=group",
      "exists": true,
      "query": {
        "program": [
          "First Aid CPR AED Group Training"
        ],
        "request_type": [
          "group"
        ]
      },
      "advances": true,
      "individual_scheduler": false
    },
    {
      "tab": "group-acls",
      "label": "Request ACLS group training",
      "href": "/request_group_session.html?program=ACLS%20Group%20Training&request_type=group",
      "exists": true,
      "query": {
        "program": [
          "ACLS Group Training"
        ],
        "request_type": [
          "group"
        ]
      },
      "advances": true,
      "individual_scheduler": false
    },
    {
      "tab": "group-pals",
      "label": "Request PALS group training",
      "href": "/request_group_session.html?program=PALS%20Group%20Training&request_type=group",
      "exists": true,
      "query": {
        "program": [
          "PALS Group Training"
        ],
        "request_type": [
          "group"
        ]
      },
      "advances": true,
      "individual_scheduler": false
    },
    {
      "tab": "group-uscg",
      "label": "Request USCG group training",
      "href": "/request_group_session.html?program=USCG%20Group%20Training&request_type=group",
      "exists": true,
      "query": {
        "program": [
          "USCG Group Training"
        ],
        "request_type": [
          "group"
        ]
      },
      "advances": true,
      "individual_scheduler": false
    }
  ],
  "group_request_page": {
    "exists": true,
    "consumes_program_query": true,
    "preserves_request_type": true,
    "has_form": true,
    "routes_to_individual_scheduler": false
  },
  "hsi_routes": [
    {
      "tab": "hsi-bls",
      "href": "/courses/hsi-bls-blended-learning-skills-session.html"
    },
    {
      "tab": "hsi-bls-fa",
      "href": "/hsi.html#hsi-bls-fa"
    },
    {
      "tab": "hsi-first-aid-cpr-aed",
      "href": "/courses/hsi-first-aid-cpr-aed.html"
    },
    {
      "tab": "hsi-cpr-aed",
      "href": "/courses/hsi-cpr-aed.html"
    }
  ],
  "semantic": {
    "pages_crawled": 153,
    "links_checked": 1728,
    "before_counts": {
      "group_flow_defects": 5,
      "wrong_family_routes": 1,
      "unnecessary_selectors": 0,
      "self_loops": 4,
      "technically_broken_links": 28,
      "semantically_wrong_links": 10
    },
    "after_counts": {
      "group_flow_defects": 0,
      "wrong_family_routes": 0,
      "unnecessary_selectors": 0,
      "self_loops": 0,
      "technically_broken_links": 0,
      "semantically_wrong_links": 0
    },
    "category_counts_after": {
      "repaired semantic route": 6,
      "valid fragment": 124,
      "valid internal": 778,
      "valid registration": 426
    },
    "unresolved_findings": 0
  },
  "determinism": {
    "checked_files": 156,
    "changed_after_second_run": [],
    "deterministic": true
  }
}
