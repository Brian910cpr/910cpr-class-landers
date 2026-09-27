import {parseIntakeFile, validId} from "../supabase/functions/canonical-session-workspace/class-record.ts";
const assertEquals = (actual: unknown, expected: unknown) => {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw Error(`Expected ${JSON.stringify(expected)}, received ${JSON.stringify(actual)}`);
};
const assertGreater = (actual: number, expected: number) => { if (!(actual > expected)) throw Error(`Expected ${actual} > ${expected}`); };

Deno.test("CSV eCard rows match a participant by exact normalized email", async () => {
  const file = new File(["eCard Code,First Name,Last Name,Email\n271277089857,Marsha,Bryant,momo0400@yahoo.com\n"], "assigned.csv", {type: "text/csv"});
  const rows = await parseIntakeFile(file, [{registration_id:"de95e2cb-b666-4233-8506-a9d561b73fa7",customer_id:"10b23afe-7201-4b55-879e-5af46531fb83",display_name:"Marsha Bryant",email:"momo0400@yahoo.com"}]);
  assertEquals(rows.length, 1);
  assertEquals(rows[0].ecard, "271277089857");
  assertEquals(rows[0].match_status, "matched");
  assertEquals(rows[0].matched_customer_id, "10b23afe-7201-4b55-879e-5af46531fb83");
});

Deno.test("ambiguous and unmatched rows are never treated as clear matches", async () => {
  const file = new File(["Name,eCard\nSame Name,271277089858\nNobody Here,271277089859\n"], "rows.csv", {type:"text/csv"});
  const people = [
    {registration_id:"1",customer_id:"1",display_name:"Same Name"},
    {registration_id:"2",customer_id:"2",display_name:"Same Name"},
  ];
  const rows = await parseIntakeFile(file, people);
  assertEquals(rows.map(row => row.match_status), ["ambiguous", "unmatched"]);
  assertEquals(rows.map(row => row.matched_customer_id), [null, null]);
});

Deno.test("standard XLSX input can be read without a runtime package dependency", async () => {
  const bytes = await Deno.readFile("data/Class Report.xlsx");
  const rows = await parseIntakeFile(new File([bytes], "Class Report.xlsx", {type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}), []);
  assertGreater(rows.length, 0);
});

Deno.test("record IDs reject filter injection", () => {
  assertEquals(validId("53d2de13-eea4-4602-ac1f-6b015249745d"), "53d2de13-eea4-4602-ac1f-6b015249745d");
});
