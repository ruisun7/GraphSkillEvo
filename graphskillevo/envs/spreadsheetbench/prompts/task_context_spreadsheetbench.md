## Task context for SpreadsheetBench

Environment name: spreadsheetbench

This environment evaluates a spreadsheet manipulation agent.

At rollout time, the agent receives a user instruction and information about an input `.xlsx` workbook. The expected behavior is to create a self-contained Python solution that reads `INPUT_PATH`, performs the requested spreadsheet manipulation, and saves the result to `OUTPUT_PATH`.

The skill should help the agent inspect workbook structure, identify sheets, headers, row and column ranges, understand the requested manipulation, and implement the transformation over actual workbook contents rather than hardcoded preview values.
