export type PacketDocument = { id:string; source:string; student_pages:number[]; descriptor_pages:number[]; student_copy_rule:"per_participant"; descriptor_copy_rule:"conditional_per_packet"; option:"print_skills_descriptors"; order:number; version:string; effective_date:string };
export type PacketRecipe = { course_keys:string[]; certifying_body:"AHA"; brand:{company_logo:string;certifying_body_logo:string}; documents:PacketDocument[] };

const files:[string,string,number[]][] = [
  ["adult","HS__Adult-CPR-AED-Skils-Testing-Sheet.pdf",[2]],
  ["child","HS__Child-CPR-AED-Skills-Checklist.pdf",[2]],
  ["infant","HS__Infant-CPR-AED-Skills-Checklist-1.pdf",[2]],
  ["first-aid","HS__First-Aid-Skills-Testing.pdf",[]],
];

export const PACKET_RECIPES:PacketRecipe[] = [{
  course_keys:["aha_heartsaver_first_aid_cpr_aed","aha_heartsaver_first_aid_cpr_aed_blended"],
  certifying_body:"AHA",
  brand:{company_logo:"https://www.910cpr.com/images/logo.png",certifying_body_logo:"https://www.910cpr.com/images/0aha.png"},
  documents:files.map(([id,name,descriptor_pages],order)=>({id,source:`heartsaver-first-aid-cpr-aed/${name}`,student_pages:[1],descriptor_pages,student_copy_rule:"per_participant",descriptor_copy_rule:"conditional_per_packet",option:"print_skills_descriptors",order:order+1,version:"issue-145-supplied-source",effective_date:"2026-09-05"})),
}];

export function recipeFor(courseKey:string){return PACKET_RECIPES.find(recipe=>recipe.course_keys.includes(courseKey))}
