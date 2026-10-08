/**
 * ClaimPilot API Service Layer
 * Seamlessly interfaces with backend endpoints with automatic fallback to mock data.
 */

const API_BASE_URL = window.CLAIM_PILOT_API_URL || 'http://localhost:8000/api';

// Pre-packaged realistic demo cases
export const DEMO_CASES = {
  laptop: {
    id: "case-laptop-8821",
    title: "Laptop Warranty Claim",
    description: "My laptop screen stopped working after 8 months and the company rejected my warranty claim saying it was physical damage.",
    createdAt: "Aug 19, 2024",
    documents: [
      { id: "doc-1", name: "Invoice.pdf", size: "2.4 MB", type: "pdf", status: "Analyzed", date: "Jan 10, 2024", summary: "Purchase: Jan 10, 2024 (Serial #SN-98214-X)" },
      { id: "doc-2", name: "Warranty.pdf", size: "1.1 MB", type: "pdf", status: "Analyzed", date: "Jan 10, 2024", summary: "Coverage details (1-year standard hardware warranty)" },
      { id: "doc-3", name: "Company_Response.pdf", size: "845 KB", type: "pdf", status: "Analyzed", date: "Aug 12, 2024", summary: "Claim rejection citing customer-induced physical damage" },
      { id: "doc-4", name: "Repair_Report.pdf", size: "1.3 MB", type: "pdf", status: "Analyzed", date: "Aug 09, 2024", summary: "Authorized tech report: 'No external impact marks observed'" },
      { id: "doc-5", name: "Laptop_Damage.jpg", size: "2.1 MB", type: "image", status: "Analyzed", date: "Aug 10, 2024", summary: "High-resolution photos showing intact chassis & display glass" }
    ],
    intelligence: {
      strengthScore: 82,
      metrics: {
        supporting: 7,
        company: 2,
        contradictions: 3,
        missing: 1
      },
      keyFindings: [
        { type: "success", text: "Potential contradiction detected between company claim and repair report." },
        { type: "danger", text: "No evidence of physical damage found in submitted documents." },
        { type: "success", text: "Warranty appears to cover the reported issue." },
        { type: "warning", text: "Original inspection photographs are missing from company file." }
      ],
      timeline: [
        { date: "Jan 10, 2024", title: "Device Purchased", desc: "Purchased laptop with 1-Year Limited Hardware Warranty (Invoice #INV-9821).", type: "neutral" },
        { date: "Aug 02, 2024", title: "Screen Failure Occurred", desc: "Internal display panel blackout reported within 8 months of normal usage.", type: "neutral" },
        { date: "Aug 05, 2024", title: "Submitted to Authorized Service Center", desc: "Diagnostic ticket opened #TKT-4412.", type: "neutral" },
        { date: "Aug 09, 2024", title: "Official Repair Report Issued", desc: "Technician explicitly noted: 'No external impact marks observed on casing or bezel.'", type: "success" },
        { date: "Aug 12, 2024", title: "Company Sent Claim Denial", desc: "Company rejected claim stating: 'Customer-induced accidental physical damage.'", type: "danger" }
      ],
      contradictions: [
        {
          id: "cnt-1",
          severity: "High (92% Impact)",
          companyClaim: {
            source: "Company_Response.pdf (Page 1)",
            statement: "Physical damage caused the internal display failure."
          },
          evidenceFact: {
            source: "Repair_Report.pdf (Section 3)",
            statement: "No external impact marks, fractures, or stress points observed."
          },
          explanation: "The company claims physical impact, but their own authorized diagnostic report certifies zero signs of physical impact."
        },
        {
          id: "cnt-2",
          severity: "High (88% Impact)",
          companyClaim: {
            source: "Support_Chat_Log.txt",
            statement: "Customer dropped device during transit."
          },
          evidenceFact: {
            source: "Laptop_Damage.jpg (Exif verified)",
            statement: "High-resolution device photos reveal pristine corners and unblemished magnesium chassis."
          },
          explanation: "Drop assertion directly refuted by multi-angle photographic evidence."
        },
        {
          id: "cnt-3",
          severity: "Medium (75% Impact)",
          companyClaim: {
            source: "Company_Response.pdf (Page 2)",
            statement: "Warranty void due to unauthorized opening."
          },
          evidenceFact: {
            source: "Repair_Report.pdf (Section 1)",
            statement: "Tamper-evident seals intact upon receipt at authorized service center."
          },
          explanation: "Service center intake inspection confirms factory seals were 100% intact."
        }
      ],
      recommendedAction: {
        headline: "Request inspection evidence from the company",
        detail: "There is no evidence of physical damage in your documents. You can request the company to provide their internal inspection photographic evidence under Section 4.2."
      },
      missingEvidence: [
        { id: "me-1", name: "Original inspection photographs", priority: "High", desc: "Technician bench teardown photos if claimed by the vendor." },
        { id: "me-2", name: "Complete inspection report", priority: "High", desc: "Full hardware diagnostic log including panel error codes." },
        { id: "me-3", name: "Technician's detailed assessment", priority: "Medium", desc: "Signed internal technician statement." },
        { id: "me-4", name: "Additional communication with support", priority: "Low", desc: "Original customer service initial intake chat." }
      ],
      generatedResponse: `Dear [Company Name] Dispute Resolution Team,

I am writing regarding the rejection of my warranty claim (Claim ID: #CLM-88421) for the laptop purchased on January 10, 2024.

Your response states that the display failure was due to "physical damage". However, the authorized repair report provided by your service center explicitly states: "No external impact marks observed." Furthermore, submitted high-resolution inspection photographs confirm the chassis and display glass are completely intact without impact distress.

Under Section 4.2 of your Warranty Agreement, internal display panel hardware defects are fully covered. Because no verifiable evidence of customer-induced physical damage has been provided, I request:
1. Immediate provision of the technician's photographic inspection evidence supporting your claim of accidental damage.
2. Re-evaluation and fulfillment of the warranty repair or replacement.

I have attached the repair report, purchase invoice, and device photos for your review. I look forward to your prompt response within 5 business days.

Sincerely,
[Claimant Name]`
    },
    graph: {
      nodes: [
        { id: "node-company", type: "claim", label: "Company Claim", text: "Physical damage caused the failure", x: 420, y: 70, color: "#ef4444" },
        { id: "node-warranty", type: "default", label: "Warranty Document", text: "Excludes accidental damage", x: 140, y: 220, color: "#3b82f6" },
        { id: "node-repair", type: "report", label: "Repair Report", text: "No external impact marks observed", x: 420, y: 270, color: "#10b981" },
        { id: "node-photos", type: "default", label: "Damage Photos", text: "Device images: Intact chassis", x: 700, y: 220, color: "#3b82f6" },
        { id: "node-invoice", type: "default", label: "Invoice", text: "Purchased Jan 10, 2024", x: 260, y: 440, color: "#3b82f6" },
        { id: "node-support", type: "default", label: "Support Messages", text: "Support ticket and communication", x: 580, y: 440, color: "#3b82f6" }
      ],
      edges: [
        { from: "node-company", to: "node-repair", relation: "CONFLICTS WITH", type: "contradicts" },
        { from: "node-company", to: "node-warranty", relation: "RELATED TO", type: "related" },
        { from: "node-company", to: "node-photos", relation: "RELATED TO", type: "related" },
        { from: "node-repair", to: "node-warranty", relation: "SUPPORTS", type: "supports" },
        { from: "node-repair", to: "node-invoice", relation: "RELATED TO", type: "related" },
        { from: "node-repair", to: "node-support", relation: "RELATED TO", type: "related" }
      ]
    }
  },

  rental: {
    id: "case-rental-1049",
    title: "Apartment Security Deposit Dispute",
    description: "Landlord withheld $1,800 security deposit alleging carpet stain and wall repainting, despite move-in checklist acknowledging pre-existing wear.",
    createdAt: "Sep 04, 2024",
    documents: [
      { id: "doc-r1", name: "Lease_Agreement.pdf", size: "1.8 MB", type: "pdf", status: "Analyzed", date: "Aug 01, 2023", summary: "Standard Lease Agreement Section 14 (Normal wear & tear excluded)" },
      { id: "doc-r2", name: "Move_In_Inspection.pdf", size: "950 KB", type: "pdf", status: "Analyzed", date: "Aug 03, 2023", summary: "Move-In Checklist: Noted minor hallway carpet discoloration" },
      { id: "doc-r3", name: "Move_Out_Photos.zip", size: "8.2 MB", type: "image", status: "Analyzed", date: "Aug 31, 2024", summary: "Time-stamped photos of pristine walls and cleaned flooring" },
      { id: "doc-r4", name: "Deposit_Deduction_Notice.pdf", size: "620 KB", type: "pdf", status: "Analyzed", date: "Sep 02, 2024", summary: "Deduction notice itemizing $1,200 carpet & $600 painting" }
    ],
    intelligence: {
      strengthScore: 89,
      metrics: { supporting: 8, company: 1, contradictions: 2, missing: 0 },
      keyFindings: [
        { type: "success", text: "Move-in inspection directly disproves landlord carpet claim." },
        { type: "danger", text: "Landlord failed to provide contractor itemized receipts within 21-day statutory limit." },
        { type: "success", text: "Tenancy exceeded 12 months, qualifying wall marks as ordinary wear & tear." }
      ],
      timeline: [
        { date: "Aug 01, 2023", title: "Lease Signed", desc: "$1,800 deposit transferred.", type: "neutral" },
        { date: "Aug 03, 2023", title: "Move-In Inspection", desc: "Pre-existing carpet wear formally signed by property manager.", type: "success" },
        { date: "Aug 31, 2024", title: "Keys Surrendered", desc: "Detailed move-out walkthrough photos taken.", type: "neutral" },
        { date: "Sep 02, 2024", title: "Deduction Notice Received", desc: "Full deposit withheld without contractor invoices.", type: "danger" }
      ],
      contradictions: [
        {
          id: "cnt-r1",
          severity: "Critical (96% Impact)",
          companyClaim: { source: "Deposit_Notice.pdf", statement: "Carpet replaced due to tenant-caused permanent staining." },
          evidenceFact: { source: "Move_In_Inspection.pdf", statement: "Property manager signed off pre-existing discoloration on day 2 of tenancy." },
          explanation: "Tenant cannot be billed for carpet conditions pre-dating their move-in."
        }
      ],
      recommendedAction: {
        headline: "Demand full deposit return under statutory tenancy law",
        detail: "State civil code prohibits deductions for pre-existing conditions and requires formal contractor receipts within 21 days."
      },
      missingEvidence: [],
      generatedResponse: `Dear Property Management,

I am writing to formally contest the deduction of $1,800 from my security deposit for Unit 4B surrendered on August 31, 2024.

The Move-In Inspection form dated August 3, 2023—countersigned by your agent—explicitly records pre-existing wear on the hallway carpet. Under state tenant law, landlords may not deduct for pre-existing defects or ordinary wear and tear. Furthermore, no contractor invoices were provided with your itemization.

I request the return of the full $1,800 security deposit within 10 business days to avoid small claims proceedings.

Sincerely,
Tenant`
    },
    graph: {
      nodes: [
        { id: "node-landlord", type: "claim", label: "Landlord Claim", text: "Tenant ruined carpet ($1,200) & walls ($600)", x: 420, y: 70, color: "#ef4444" },
        { id: "node-lease", type: "default", label: "Lease Agreement", text: "Wear & tear strictly excluded", x: 140, y: 220, color: "#3b82f6" },
        { id: "node-movein", type: "report", label: "Move-In Checklist", text: "Pre-existing carpet wear noted", x: 420, y: 270, color: "#10b981" },
        { id: "node-photos", type: "default", label: "Move-Out Photos", text: "Pristine cleaned premises", x: 700, y: 220, color: "#3b82f6" }
      ],
      edges: [
        { from: "node-landlord", to: "node-movein", relation: "CONFLICTS WITH", type: "contradicts" },
        { from: "node-landlord", to: "node-lease", relation: "CONFLICTS WITH", type: "contradicts" },
        { from: "node-movein", to: "node-photos", relation: "SUPPORTS", type: "supports" }
      ]
    }
  }
};

export const ClaimPilotAPI = {
  /**
   * Create a new case
   */
  async createCase(caseData) {
    try {
      const response = await fetch(`${API_BASE_URL}/cases`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(caseData)
      });
      if (response.ok) return await response.json();
    } catch (e) {
      console.warn("Backend API not reachable, using local mock data fallback.", e);
    }
    return {
      caseId: `case-${Date.now()}`,
      title: caseData.title || "Laptop Warranty Claim",
      description: caseData.description || "",
      status: "created"
    };
  },

  /**
   * Upload documents to a case
   */
  async uploadDocuments(caseId, files) {
    try {
      const formData = new FormData();
      files.forEach(f => formData.append('files', f));
      const response = await fetch(`${API_BASE_URL}/cases/${caseId}/documents`, {
        method: 'POST',
        body: formData
      });
      if (response.ok) return await response.json();
    } catch (e) {
      console.warn("Backend API not reachable, mocking document upload.", e);
    }
    return { success: true, count: files.length };
  },

  /**
   * Fetch case intelligence and graph
   */
  async getCaseAnalysis(caseId = "laptop") {
    try {
      const response = await fetch(`${API_BASE_URL}/cases/${caseId}/analysis`);
      if (response.ok) return await response.json();
    } catch (e) {
      console.warn("Backend API offline. Serving dynamic demo case analysis.", e);
    }
    return DEMO_CASES[caseId] || DEMO_CASES.laptop;
  },

  /**
   * Request response regeneration with custom tone
   */
  async generateResponse(caseId, tone = "firm") {
    try {
      const response = await fetch(`${API_BASE_URL}/cases/${caseId}/generate-response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tone })
      });
      if (response.ok) return await response.json();
    } catch (e) {
      console.warn("Using offline generator for tone:", tone);
    }
    const current = DEMO_CASES.laptop.intelligence.generatedResponse;
    if (tone === "formal") {
      return { response: current.replace("Dear [Company Name]", "Attention: Formal Legal & Dispute Bureau, [Company Name]") };
    } else if (tone === "concise") {
      return {
        response: `To [Company Name] Claims Team,\n\nRe: Claim #CLM-88421 Denial Contest.\n\nYour denial asserts physical impact damage. However, the Authorized Repair Report explicitly confirms: 'No external impact marks observed.' Tamper seals and outer chassis remain flawless.\n\nPlease furnish photographic evidence of internal damage or approve repair/replacement per Warranty Clause 4.2 within 5 days.\n\nRespectfully,\n[Claimant Name]`
      };
    }
    return { response: current };
  }
};
