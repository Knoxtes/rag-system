"""
Smart query router for market-specific folder structures
Analyzes user queries and routes them optimally based on folder organization
"""

import re
from config_market_specific import (
    KNOWN_MARKETS, 
    FOLDER_CATEGORIES, 
    TIME_PATTERNS,
    MARKET_QUERY_EXPANSIONS,
    FOLDER_ALIASES
)


class QueryRouter:
    """
    Intelligently routes queries based on detected markets, time periods, and categories.
    Optimized for hierarchical folder structures.
    """
    
    def __init__(self):
        self.markets = KNOWN_MARKETS
        self.categories = FOLDER_CATEGORIES
        self.time_patterns = TIME_PATTERNS
        
    def analyze_query(self, query):
        """
        Analyze a user query and extract:
        - Markets mentioned
        - Time periods (years, quarters, months)
        - Categories (sales, marketing, etc.)
        - Suggested folder paths
        
        Returns a routing suggestion for optimal search
        """
        query_lower = query.lower()
        
        analysis = {
            "original_query": query,
            "detected_markets": [],
            "detected_years": [],
            "detected_months": [],
            "detected_categories": [],
            "suggested_folder_pattern": None,
            "search_strategy": "general",  # or "folder_specific", "time_filtered", "market_specific"
            "enhanced_query": query
        }
        
        # Detect markets
        for market in self.markets:
            if market.lower() in query_lower:
                analysis["detected_markets"].append(market)
        
        # Detect years
        years = re.findall(self.time_patterns["years"], query)
        analysis["detected_years"] = years
        
        # Detect months
        months = re.findall(self.time_patterns["months"], query, re.IGNORECASE)
        analysis["detected_months"] = months
        
        # Detect categories
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    analysis["detected_categories"].append(category)
                    break
        
        # Build suggested folder pattern
        folder_parts = []
        
        # Add market if detected
        if analysis["detected_markets"]:
            folder_parts.append(analysis["detected_markets"][0])
        
        # Add year if detected
        if analysis["detected_years"]:
            folder_parts.append(analysis["detected_years"][0])
        
        # Add month if detected
        if analysis["detected_months"]:
            folder_parts.append(analysis["detected_months"][0])
        
        # Add category if detected
        if analysis["detected_categories"]:
            cat = analysis["detected_categories"][0]
            if cat in self.categories:
                folder_parts.append(self.categories[cat][0])  # First keyword
        
        # Determine search strategy
        if folder_parts:
            analysis["suggested_folder_pattern"] = "/".join(folder_parts)
            analysis["search_strategy"] = "folder_specific"
        elif analysis["detected_years"] or analysis["detected_months"]:
            analysis["search_strategy"] = "time_filtered"
            if analysis["detected_years"]:
                analysis["suggested_folder_pattern"] = analysis["detected_years"][0]
        elif analysis["detected_markets"]:
            analysis["search_strategy"] = "market_specific"
            analysis["suggested_folder_pattern"] = analysis["detected_markets"][0]
        
        # Enhance query with synonyms
        enhanced_query = self._enhance_query(query, analysis)
        analysis["enhanced_query"] = enhanced_query
        
        return analysis
    
    def _enhance_query(self, query, analysis):
        """Add context-specific synonyms based on detected patterns"""
        enhanced = query
        
        # Add market names if markets detected
        if analysis["detected_markets"]:
            market_list = " ".join(analysis["detected_markets"])
            if "market" in query.lower():
                enhanced = f"{query} {market_list}"
        
        # Add category synonyms
        for category in analysis["detected_categories"]:
            if category in MARKET_QUERY_EXPANSIONS:
                template = MARKET_QUERY_EXPANSIONS[category]
                if category in query.lower():
                    # Already contains category, skip
                    continue
        
        return enhanced
    
    def suggest_tool(self, analysis):
        """
        Suggest which tool to use based on analysis
        Returns: ("tool_name", {params})
        """
        if analysis["search_strategy"] == "folder_specific" and analysis["suggested_folder_pattern"]:
            # Use folder search
            return ("search_folder", {
                "folder_pattern": analysis["suggested_folder_pattern"],
                "query": analysis["enhanced_query"]
            })
        elif analysis["detected_years"] and len(analysis["detected_years"]) > 0:
            # Time-based search
            return ("search_folder", {
                "folder_pattern": analysis["detected_years"][0],
                "query": analysis["enhanced_query"]
            })
        else:
            # General RAG search
            return ("rag_search", {
                "query": analysis["enhanced_query"]
            })


# Example usage
if __name__ == "__main__":
    router = QueryRouter()
    
    test_queries = [
        "Please give summaries of all projection CSV's in the 2025 Projections Folder for 1-JANUARY",
        "What packages does Elmira have for Christmas 2025?",
        "Show me sales presentations for Mansfield",
        "What's in the Wall of Wisdom for B2B selling?",
        "List all 2026 promotions",
        "Find media kits for all markets"
    ]
    
    print("=" * 80)
    print("QUERY ROUTING ANALYSIS")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n📝 Query: \"{query}\"")
        analysis = router.analyze_query(query)
        tool, params = router.suggest_tool(analysis)
        
        print(f"   Markets: {analysis['detected_markets']}")
        print(f"   Years: {analysis['detected_years']}")
        print(f"   Months: {analysis['detected_months']}")
        print(f"   Categories: {analysis['detected_categories']}")
        print(f"   Strategy: {analysis['search_strategy']}")
        print(f"   Folder Pattern: {analysis['suggested_folder_pattern']}")
        print(f"   → Recommended: {tool}({params})")
        print("   " + "-" * 70)
