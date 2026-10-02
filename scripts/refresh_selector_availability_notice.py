"""Refresh only generated selector message blocks from the authoritative template."""
from pathlib import Path
import re
from scripts.block_start_time_selector import load_block_schedule_page_configs
ROOT=Path(__file__).resolve().parents[1]
def main():
 source=(ROOT/'scripts/build_bls_block_schedule_pilot.py').read_text(encoding='utf-8')
 match=re.search(r'    function setAvailabilityMessage\(message\) \{\{.*?\n    \}\}',source,re.S)
 if not match:raise ValueError('Authoritative notice setter not found')
 setter=match.group().replace('{{','{').replace('}}','}')
 configs=load_block_schedule_page_configs()
 keys=('bls','heartsaver','acls','pals','arc','hsi','family_cpr','uscg_first_aid_cpr_aed');updates=[]
 for key in keys:
  path=(ROOT/configs[key]['output_path']).resolve()
  if not path.is_relative_to((ROOT/'docs').resolve()):raise ValueError('Unexpected output path')
  text=path.read_bytes().decode('utf-8');eol='\r\n' if '\r\n' in text else '\n'
  start=text.index('    function setAvailabilityMessage(message) {');end=text.index('    function renderAvailabilityPlaceholder',start)
  replacement=setter.replace('\n',eol)+eol+eol
  updated=text[:start]+replacement+text[end:]
  if updated!=text:updates.append((path,updated))
 for path,text in updates:path.write_bytes(text.encode('utf-8'));print(path.relative_to(ROOT))
 print(f'Updated {len(updates)} selector HTML notice blocks; no inventory/feed generation.')
if __name__=='__main__':main()
