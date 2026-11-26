# PaperDesk check report

- File: `samples/test_paper_flawed.docx`
- Rule set: IEEE conference (draft rules, verify against the official template)
- Result: **9 errors, 3 warnings**

## Errors (fix before submitting)

1. **Margin**: Top margin is 1.00 in; expected 0.75 in.
   - Where: document
   - Fix: Set the top margin to 0.75 in.
2. **Margin**: Left margin is 1.00 in; expected 0.625 in.
   - Where: document
   - Fix: Set the left margin to 0.625 in.
3. **Margin**: Right margin is 1.00 in; expected 0.625 in.
   - Where: document
   - Fix: Set the right margin to 0.625 in.
4. **Body text style**: Found font Arial, size 12.0; expected Times New Roman 10 pt.
   - Where: paragraph 5: "Preparing a manuscript for submission involves many small..."
   - Fix: Apply the body text style to this paragraph.
5. **Abstract length**: Abstract has 16 words; expected 150-250.
   - Where: paragraph 3
   - Fix: Expand or shorten the abstract to fit the range.
6. **Index terms**: No Index Terms / keywords line found.
   - Where: document
   - Fix: Add an 'Index Terms' line after the abstract.
7. **Heading numbering**: Heading numbered V but section 4 was expected.
   - Where: paragraph 15: "V. CHECKS IMPLEMENTED"
   - Fix: Renumber headings in order (I, II, III, ...).
8. **Citation without reference**: Citation [6] has no entry in the reference list.
   - Where: paragraph 10
   - Fix: Add reference [6] or correct the citation number.
9. **Figure referenced but missing**: Fig. 2 is mentioned but no caption 'Fig. 2.' exists.
   - Where: paragraph 14
   - Fix: Insert the figure with a caption or fix the number.

## Warnings (please review)

1. **Reference never cited**: Reference [3] is not cited anywhere in the text.
   - Where: reference [3]
   - Fix: Cite it where relevant or remove it.
2. **Table not referenced**: Table I is never mentioned in the text.
   - Where: Table I
   - Fix: Refer to it in the text.
3. **Double space**: 2 double space(s) found.
   - Where: paragraph 6: "A checker should be predictable. It should report what it..."
   - Fix: Replace double spaces with single spaces.

---
This report lists problems only. It did not change your document. Rules are a draft; confirm them against the conference's own instructions.