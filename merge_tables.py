
import re

INPUT_FILE = '/home/ubuntu/Documents/Knight-Note/China_A_Discipline_Evaluation.md'
OUTPUT_FILE = '/home/ubuntu/Documents/Knight-Note/China_A_Discipline_Evaluation_Merged.md'

def parse_table_line(line):
    # | col1 | col2 | ... |
    parts = [p.strip() for p in line.strip().split('|')]
    # Remove empty first/last from split if they are empty strings
    if parts and parts[0] == '':
        parts.pop(0)
    if parts and parts[-1] == '':
        parts.pop()
    return parts

def merge_tables():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    
    current_discipline_rows = []
    current_grade = None
    in_discipline_section = False
    
    # Regex to identify discipline headers (e.g. ## 一、...)
    # But NOT "## 六、使用建议" or similar if we strictly want to exclude it, 
    # though the prompt implies merging for disciplines. 
    # Looking at file, "Hex" is advice. We can treat headers starting with numbers as disciplines, EXCEPT section 6?
    # Actually, section 6 has no tables to merge in the same way, or maybe check content.
    # Let's rely on standard logic: collect rows if we see "### A..." headers.
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check for Section Header
        if stripped.startswith('## '):
            # If we were collecting rows for a previous discipline, dump them now
            if current_discipline_rows:
                # Dump table
                output_lines.append(f"| 学校 | 等级 | 省市 |\n")
                output_lines.append(f"|---|---|---|\n")
                for row in current_discipline_rows:
                    output_lines.append(f"| {row[0]} | {row[1]} | {row[2]} |\n")
                output_lines.append("\n") # Blank line after table
                current_discipline_rows = []
            
            in_discipline_section = True
            output_lines.append(line)
            i += 1
            continue

        # Check for Grade Header (### A...)
        # We want to SKIP printing this header to output, but use it to set current_grade
        if stripped.startswith('### '):
            header_text = stripped.replace('###', '').strip()
            # Check if it looks like a grade header (A+, A, A-)
            # Some might have Chinese text? The file shows "A+（顶尖）", "A", "A-"
            if 'A' in header_text:
                if 'A+' in header_text:
                    current_grade = 'A+'
                elif 'A-' in header_text:
                    current_grade = 'A-'
                elif header_text.startswith('A'): # strict 'A' or 'A ...'
                    current_grade = 'A'
                
                # Consume this line (don't print it)
                i += 1
                continue
            else:
                # Other H3 headers? Print them if any
                output_lines.append(line)
                i += 1
                continue

        # Check for Table
        if stripped.startswith('|'):
            # It's a table line.
            # is it a separator? |---|
            if '---' in stripped:
                i += 1
                continue
            
            parts = parse_table_line(line)
            # Check if header row? "学校" in parts
            if '学校' in parts:
                i += 1
                continue
            
            # Data row
            if len(parts) > 0:
                # Normalize logic
                school = parts[0]
                grade = current_grade
                location = ""
                
                # Case 1: | 学校 | 学科 | 等级 | 所在省市 | (4 cols)
                if len(parts) == 4:
                    # parts[1] is subject, we drop it
                    # parts[2] is grade from table, usually matches current_grade
                    # parts[3] is location
                    grade_in_table = parts[2]
                    location = parts[3]
                    # If column says grade, use it, otherwise fallback to section header
                    if not grade: grade = grade_in_table
                
                # Case 2: | 学校 | 等级 | 省市 | (3 cols)
                elif len(parts) == 3:
                     # Check if middle col looks like grade
                    if 'A' in parts[1]:
                        grade_in_table = parts[1]
                        location = parts[2]
                        if not grade: grade = grade_in_table
                    else:
                        # Maybe | School | Province | (Wait, 3 cols?)
                        # Actually look at AI section: | 学校 | 省市 | (2 cols)
                        pass

                # Case 3: | 学校 | 省市 | (2 cols)
                elif len(parts) == 2:
                    location = parts[1]
                
                if current_grade and grade is None:
                     grade = current_grade
                
                if grade and location:
                    current_discipline_rows.append((school, grade, location))
            
            i += 1
            continue

        # Empty lines or text between tables
        # If we are inside a discipline and have pending rows, we might want to keep collecting?
        # But we also need to preserve text like quotes "> ...". 
        # The prompt says "combine each section into one table".
        # We should NOT print empty lines that were between the split tables if we are merging them.
        # But we MUST print quotes or descriptions that appear at the start of section.
        
        # Heuristic: 
        # If we have current_discipline_rows, and we hit text that is NOT a table and NOT a header...
        # It might be end of section or some footer text. 
        # Actually in this file, the text is usually at the TOP (quotes).
        # The tables follow immediately. 
        # There are lines "---" separating sections.
        
        if stripped == '---':
             # Separator. Dump current table if any.
            if current_discipline_rows:
                output_lines.append(f"| 学校 | 等级 | 省市 |\n")
                output_lines.append(f"|---|---|---|\n")
                for row in current_discipline_rows:
                    output_lines.append(f"| {row[0]} | {row[1]} | {row[2]} |\n")
                output_lines.append("\n")
                current_discipline_rows = []
            output_lines.append(line)
        else:
             # Regular text. 
             # If it's a blank line, maybe skip if we are in "table merging mode" (between A+ and A)?
             # To be safe: if we have active rows, only print non-blank lines if they are significant.
             # But keeping it simple: just print everything that isn't a table part index.
             # EXCEPT: verify if this text was between tables.
             # If we blindly print, the merged table will appear at the end of the section, 
             # and the text (if any) that was between tables will appear before it? No.
             
             # Better approach: Buffer everything.
             # When detailed parsing is hard, just parse the WHOLE file into a structured object structure first, then render.
             # But for this task, linear scan is okay if we are careful.
             
             # If we are in a merged block, we want to suppress the intermediate text if it's just whitespace?
             # The input file only has whitespace between tables usually.
             
             if not line.strip() and current_discipline_rows:
                 # Skip blank lines while collecting rows to avoid gaps?
                 # We will add our own blank line after the big table.
                 pass
             else:
                 output_lines.append(line)
        
        i += 1
    
    # End of loop. Dump remaining.
    if current_discipline_rows:
        output_lines.append(f"| 学校 | 等级 | 省市 |\n")
        output_lines.append(f"|---|---|---|\n")
        for row in current_discipline_rows:
            output_lines.append(f"| {row[0]} | {row[1]} | {row[2]} |\n")
        output_lines.append("\n")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

if __name__ == "__main__":
    merge_tables()
