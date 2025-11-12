# Unified RAG System Documentation

## 🌟 Overview

The **Unified RAG System** combines all your indexed Google Drive folders into one seamless chat experience. Instead of choosing which folder to search, the system intelligently analyzes your question and automatically searches the most relevant folders first, while still including results from all collections.

## ✨ Key Features

### 1. **Smart Intent Analysis**
- Automatically categorizes queries by topic (HR, Creative, Admin, etc.)
- Uses keyword mapping to determine folder relevance
- Scores folders based on query content

### 2. **Intelligent Search Routing**
- Searches most relevant folders first
- Boosts relevance scores based on folder matching
- Cross-collection search with unified results

### 3. **Enhanced Response Format**
- Results grouped by source folder
- Google Drive links for direct document access
- Relevance scoring with folder-aware boosting
- Source attribution for every result

### 4. **Folder-Aware Context**
- Maintains knowledge of document origins
- Preserves organizational structure information
- Optimizes search without losing comprehensiveness

## 🔧 How It Works

### Intent Classification
The system analyzes your query for keywords that indicate which folder might be most relevant:

**HR/Human Resources Keywords:**
- `hr`, `employee`, `benefits`, `vacation`, `pto`, `policy`, `handbook`, `payroll`, `hiring`, `onboarding`, `training`, `performance review`, `health insurance`, `retirement`, `401k`, `holidays`

**Creative/Marketing Keywords:**
- `creative`, `marketing`, `design`, `brand`, `logo`, `website`, `video`, `photography`, `graphics`, `advertising`, `campaign`, `content`, `social media`, `production`, `samples`, `portfolio`

**Admin/Traffic Keywords:**
- `admin`, `administration`, `traffic`, `operations`, `procedures`, `workflow`, `management`, `coordination`, `scheduling`, `logistics`, `billing`, `invoicing`

**And more for Sales, Finance, Legal, etc.**

### Search Process
1. **Query Analysis**: System analyzes your question to determine relevance to each folder
2. **Folder Scoring**: Each folder gets a relevance score (0-1) based on keyword matches
3. **Prioritized Search**: Searches folders in order of relevance, most relevant first
4. **Result Boosting**: Results from highly relevant folders get boosted scores
5. **Unified Results**: All results combined and sorted by boosted relevance

### Response Formatting
- Results grouped by source folder for organization
- Top results from each relevant folder included
- Google Drive links for immediate document access
- Clear source attribution and relevance scores

## 🚀 Usage

### From Main Menu
```bash
python main.py
# Select option 3: "🌟 Unified Q&A System (Smart search across ALL folders)"
```

### Direct Access
```bash
python unified_rag_system.py
```

### Programmatic Usage
```python
from unified_rag_system import UnifiedRAGSystem

# Initialize system
unified_system = UnifiedRAGSystem()
unified_system.initialize_rag_systems()

# Search with intelligent routing
response = unified_system.unified_query("What are the vacation policies?")
print(response)
```

## 🔍 Example Queries and Routing

| Query | Primary Folder | Secondary Folders |
|-------|---------------|------------------|
| "vacation policy" | HR | All others |
| "logo guidelines" | Creative | Marketing, Admin |
| "employee handbook" | HR | Admin, Legal |
| "design samples" | Creative | Marketing |
| "billing procedures" | Admin | Finance |

## 🆚 Unified vs Legacy Mode

### Unified Mode (Recommended)
- ✅ Search across all folders automatically
- ✅ Intelligent folder prioritization
- ✅ Comprehensive results from all sources
- ✅ No need to choose which folder to search
- ✅ Smart relevance boosting
- ✅ Folder-aware source attribution

### Legacy Mode (Individual Folders)
- ⚠️ Must choose specific folder before searching
- ⚠️ Only searches selected folder
- ⚠️ Might miss relevant documents in other folders
- ✅ Focused results from chosen folder only
- ✅ Simpler for very specific folder queries

## 🛠️ Configuration

The system automatically builds keyword mappings based on your indexed folder names and locations. You can customize the keyword mapping by modifying the `build_folder_keyword_map()` method in `unified_rag_system.py`.

### Adding Custom Keywords
```python
# In build_folder_keyword_map() method
if 'your_custom_folder' in folder_name:
    keywords.extend([
        'custom_keyword1', 'custom_keyword2', 
        'domain_specific_term', 'company_specific_term'
    ])
```

## 📊 Performance Benefits

1. **Better User Experience**: No folder selection required
2. **Comprehensive Search**: Never miss relevant documents
3. **Smart Prioritization**: Most relevant results first
4. **Organized Results**: Clear folder-based organization
5. **Source Attribution**: Always know where results come from

## 🔧 Troubleshooting

### No Results Found
- Ensure folders are properly indexed
- Check that `indexed_folders.json` exists and is valid
- Verify ChromaDB collections are accessible

### Poor Folder Routing
- Review keyword mapping in `build_folder_keyword_map()`
- Add domain-specific keywords for your organization
- Check folder naming conventions

### Slow Performance
- Limit `max_results_per_folder` parameter
- Reduce total result count in `format_response_with_sources()`
- Consider indexing optimization

## 📈 Future Enhancements

- **Machine Learning Intent Classification**: Replace keyword-based routing with ML models
- **User Feedback Learning**: Improve routing based on user interactions
- **Query Expansion**: Automatic query enhancement for better results
- **Advanced Ranking**: Sophisticated relevance scoring algorithms
- **Performance Optimization**: Parallel search across collections

## 🤝 Integration

The unified system works seamlessly with:
- ✅ Existing Google Drive authentication
- ✅ Current ChromaDB vector storage
- ✅ Enhanced RAG system with Google Drive links
- ✅ All existing indexing and document processing
- ✅ Streamlit web interface (future enhancement)

---

*For technical implementation details, see `unified_rag_system.py`*
*For testing and validation, run `test_unified_system.py`*