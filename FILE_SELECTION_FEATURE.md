# 📄 File-Specific Query Feature

## What's New

You can now click on any file in the Google Drive browser (right panel) to ask questions specifically about that file!

## How It Works

### 1. **Select a File**
- Browse folders in the right panel
- Click on any **file** (not folders)
- The file will be highlighted with a blue border
- A blue indicator appears above the chat input showing which file is selected

### 2. **Ask Questions About That File**
- Type your question as usual
- The system will **only search within the selected file**
- You'll get answers specific to that document

### 3. **Clear Selection**
- Click the **×** button on the blue indicator above the input
- Or click on another file to switch to a different one
- Or just ask a general question - the file will remain selected until cleared

## Example Use Cases

### CSV Files
- Click on "Altoona-6 Month Sales Projection.csv" in the January folder
- Ask: "What is the January 2025 sales total?"
- Get data **only from that specific CSV file**

### Policy Documents
- Click on "Employee Handbook.pdf"
- Ask: "What is the vacation policy?"
- Get information **only from that handbook**

### Monthly Reports
- Click on "Q4 2024 Report.docx"
- Ask: "What were the main achievements?"
- Get insights **only from that specific report**

## Visual Indicators

### Selected File
- **Blue highlight** around the file in the browser
- **Blue border and background** on the file name

### Active Query
- **Blue banner** above chat input showing:
  ```
  📄 Asking about: [filename]  ×
  ```

## Technical Details

### Frontend Changes
- `App.tsx`: Added `selectedFile` state
- File click handler updates selection
- Visual indicators show which file is selected
- Clear button to remove selection

### Backend Changes
- `chat_api.py`: Accepts `file_id` parameter in chat endpoint
- `rag_system.py`: Filters vector search by `file_id`
- `vector_store.py`: Supports ChromaDB `where` filters

### How Filtering Works
When a file is selected, the system:
1. Extracts the Google Drive `file_id` from the clicked file
2. Sends it with your question to the backend
3. Backend adds a filter: `where={"file_id": "..."}`
4. ChromaDB only searches chunks from that file
5. AI generates answer based only on that file's content

## Benefits

✅ **Precision**: Get answers from specific documents  
✅ **Disambiguation**: When multiple files have similar names, pick the exact one  
✅ **Context**: Understand which source your answer came from  
✅ **Speed**: Faster searches with smaller scope  

## Limitations

- Only works with **indexed files** (files must be in the vector database)
- Works with both single collections and multi-collection mode
- If file has no relevant content, you may get no results

## Testing

1. Start the chat system: `python start_chat_system.py`
2. Open: http://localhost:5000
3. Expand a folder in the right panel
4. Click on a file
5. Ask a question about it
6. Verify the answer comes only from that file

## Compatibility

- ✅ Works with CSV files (including new single-chunk approach)
- ✅ Works with PDFs, Word docs, Excel files
- ✅ Works with both single and multi-collection searches
- ✅ Preserves all existing functionality when no file is selected
