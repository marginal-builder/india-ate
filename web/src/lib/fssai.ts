import type { DecodedFSSAI14 } from "./types";

export const FSSAI_LENGTH = 14;
export const TIER_LICENSE_DIGIT = "1";
export const TIER_BASIC_REG_DIGIT = "2";
export const CENTRAL_STATE_CODE = "00";
export const YEAR_CENTURY_BASE = 2000;

export const STATE_UT_CODES: Record<string, string> = {
  "00": "Central",
  "01": "Andhra Pradesh",
  "02": "Arunachal Pradesh",
  "03": "Assam",
  "04": "Bihar",
  "05": "Chhattisgarh",
  "06": "Goa",
  "07": "Gujarat",
  "08": "Haryana",
  "09": "Himachal Pradesh",
  "10": "Jammu & Kashmir",
  "11": "Jharkhand",
  "12": "Karnataka",
  "13": "Kerala",
  "14": "Madhya Pradesh",
  "15": "Maharashtra",
  "16": "Manipur",
  "17": "Meghalaya",
  "18": "Mizoram",
  "19": "Nagaland",
  "20": "Odisha",
  "21": "Punjab",
  "22": "Rajasthan",
  "23": "Sikkim",
  "24": "Tamil Nadu",
  "25": "Tripura",
  "26": "Uttarakhand",
  "27": "Uttar Pradesh",
  "28": "West Bengal",
  "29": "Andaman & Nicobar Islands",
  "30": "Chandigarh",
  "31": "Dadra & Nagar Haveli",
  "32": "Daman & Diu",
  "33": "Delhi",
  "34": "Lakshadweep",
  "35": "Puducherry",
  "36": "Telangana",
  "37": "Ladakh",
};

export const CENTRAL_RO_DO_CODES: Record<string, [string, string]> = {
  "021": ["RO Mumbai", "Gujarat"],
  "022": ["RO Mumbai", "Maharashtra"],
  "023": ["RO Mumbai", "Dadra & Nagar Haveli"],
  "024": ["RO Mumbai", "Daman & Diu"],
  "025": ["RO Mumbai", "Goa"],
  "026": ["RO Mumbai", "Madhya Pradesh"],
  "031": ["RO Kolkata", "West Bengal"],
  "032": ["RO Kolkata", "Odisha"],
  "033": ["RO Kolkata", "Bihar"],
  "034": ["RO Kolkata", "Jharkhand"],
  "035": ["RO Kolkata", "Sikkim"],
  "036": ["RO Kolkata", "Andaman & Nicobar Islands"],
  "037": ["RO Kolkata", "Chhattisgarh"],
  "041": ["RO Chennai", "Kerala"],
  "042": ["RO Chennai", "Tamil Nadu"],
  "043": ["RO Chennai", "Karnataka"],
  "044": ["RO Chennai", "Andhra Pradesh"],
  "045": ["RO Chennai", "Puducherry"],
  "046": ["RO Chennai", "Lakshadweep"],
  "071": ["RO Guwahati", "Assam"],
  "072": ["RO Guwahati", "Arunachal Pradesh"],
  "073": ["RO Guwahati", "Tripura"],
  "074": ["RO Guwahati", "Manipur"],
  "075": ["RO Guwahati", "Mizoram"],
  "076": ["RO Guwahati", "Meghalaya"],
  "077": ["RO Guwahati", "Nagaland"],
};

export function normalizeAndValidateFssai14(rawValue: string): string {
  const cleaned = rawValue.trim();
  if (cleaned.length !== FSSAI_LENGTH || !/^[0-9]{14}$/.test(cleaned)) {
    throw new Error("FSSAI ID must be a 14-digit numeric string");
  }
  const tierDigit = cleaned[0];
  if (tierDigit !== TIER_LICENSE_DIGIT && tierDigit !== TIER_BASIC_REG_DIGIT) {
    throw new Error(`Invalid FSSAI license tier digit: '${tierDigit}'`);
  }
  const stateCode = cleaned.slice(1, 3);
  if (!(stateCode in STATE_UT_CODES)) {
    throw new Error(`Unknown FSSAI state or UT code: '${stateCode}'`);
  }
  return cleaned;
}

export function decodeFssai14Offline(rawValue: string): DecodedFSSAI14 {
  const cleaned = normalizeAndValidateFssai14(rawValue);
  const tierDigit = cleaned[0];
  const stateCode = cleaned.slice(1, 3);
  const yearDigits = cleaned.slice(3, 5);
  const officerCode = cleaned.slice(5, 8);
  const serial = cleaned.slice(8, 14);

  const centralMatch =
    stateCode === CENTRAL_STATE_CODE
      ? CENTRAL_RO_DO_CODES[officerCode] ?? null
      : null;

  return {
    tier: tierDigit === TIER_LICENSE_DIGIT ? "license" : "basic_registration",
    pre_inspection_exempt_post_apr2026: tierDigit === TIER_BASIC_REG_DIGIT,
    authority_scope: stateCode === CENTRAL_STATE_CODE ? "central" : "state_or_ut",
    state_code: stateCode,
    state_name: STATE_UT_CODES[stateCode],
    registration_year: YEAR_CENTURY_BASE + Number.parseInt(yearDigits, 10),
    officer_code: officerCode,
    central_regional_office: centralMatch ? centralMatch[0] : null,
    officer_jurisdiction_state: centralMatch ? centralMatch[1] : null,
    serial,
  };
}

export function describeLicenseTierFact(decoded: DecodedFSSAI14): string {
  if (decoded.tier === "basic_registration") {
    return "Basic Registration (Post-Apr 1, 2026 rule: up to ₹1.5 Cr annual turnover, no pre-inspection, perpetual validity)";
  }
  if (decoded.authority_scope === "central") {
    return "Central License (Tier 1 — FSSAI Central Authority)";
  }
  return `State/UT License (Tier 1 — ${decoded.state_name})`;
}
