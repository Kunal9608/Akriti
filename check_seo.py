import os
import sys
from pathlib import Path
import re

def check_html_file(file_path, is_public):
    errors = []
    warnings = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Check title tag
    title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    if not title_match:
        errors.append("Missing <title> tag")
    elif not title_match.group(1).strip():
        errors.append("<title> tag is empty")

    # 2. Check description/robots meta tags
    if is_public:
        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
        if not desc_match:
            errors.append("Public page is missing <meta name=\"description\"> tag for SEO")
        elif not desc_match.group(1).strip():
            errors.append("<meta name=\"description\"> is empty")
    else:
        robots_match = re.search(r'<meta\s+name=["\']robots["\']\s+content=["\']noindex,\s*nofollow["\']', content, re.IGNORECASE)
        if not robots_match:
            errors.append("Secure/Private page is missing <meta name=\"robots\" content=\"noindex, nofollow\">")

    # 3. Check <h1> count
    h1_matches = re.findall(r"<h1\b", content, re.IGNORECASE)
    if len(h1_matches) == 0:
        warnings.append("Missing <h1> tag (SEO structural hierarchy recommends exactly one per page)")
    elif len(h1_matches) > 1:
        warnings.append(f"Multiple <h1> tags found ({len(h1_matches)} tags) — should have exactly one per page")

    # 4. Check unique IDs on inputs
    inputs = re.findall(r"<input\s+[^>]*>", content, re.IGNORECASE)
    ids = []
    for inp in inputs:
        id_match = re.search(r'\bid=["\'](.*?)["\']', inp, re.IGNORECASE)
        if not id_match:
            # Skeletons or auxiliary inputs might not have IDs, warning only
            name_match = re.search(r'\bname=["\'](.*?)["\']', inp, re.IGNORECASE)
            inp_desc = name_match.group(0) if name_match else inp[:30]
            warnings.append(f"Input element is missing an 'id' attribute: {inp_desc}")
        else:
            val = id_match.group(1)
            if val in ids:
                errors.append(f"Duplicate 'id' attribute value found: '{val}'")
            ids.append(val)

    return errors, warnings

def main():
    print("=" * 60)
    print("  Akriti Pathology Lab — SEO Compliance Checker")
    print("=" * 60)
    
    frontend_dir = Path(__file__).parent / "frontend"
    if not frontend_dir.exists():
        print(f"[ERROR] Frontend directory not found at: {frontend_dir}")
        sys.exit(1)

    html_files = list(frontend_dir.glob("**/*.html"))
    print(f"Scanning {len(html_files)} HTML views...")
    
    total_errors = 0
    total_warnings = 0
    
    for file_path in sorted(html_files):
        relative_path = file_path.relative_to(frontend_dir)
        is_public = (file_path.name == "index.html" and file_path.parent == frontend_dir)
        
        errors, warnings = check_html_file(file_path, is_public)
        
        if errors or warnings:
            status = "ERROR" if errors else "WARNING"
            print(f"\n[{status}] File: frontend/{relative_path}")
            for err in errors:
                print(f"   - ERROR: {err}")
                total_errors += 1
            for warn in warnings:
                print(f"   - WARNING: {warn}")
                total_warnings += 1
        else:
            print(f"[OK] PASS: frontend/{relative_path}")

    print("\n" + "=" * 60)
    print(f"Scan complete: {total_errors} errors, {total_warnings} warnings.")
    print("=" * 60)
    
    if total_errors > 0:
        print("[FAIL] Please fix the SEO errors listed above.")
        sys.exit(1)
    else:
        print("[SUCCESS] All pages passed SEO compliance checks!")
        sys.exit(0)

if __name__ == "__main__":
    main()
