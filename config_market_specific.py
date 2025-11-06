# config_market_specific.py - Market-specific optimizations

"""
This configuration adds market-aware and time-aware search capabilities
based on your folder structure analysis.
"""

# Market names detected in your structure (18 total!)
KNOWN_MARKETS = [
    "Altoona",
    "Bloomsburg",
    "Bowling Green",
    "DuBois",
    "Elmira",
    "Frankfort KY",
    "Hornell",
    "Johnstown",
    "Lebanon",
    "Lewistown",
    "Mansfield",
    "NWPA",
    "Olean",
    "Parkersburg",
    "Selinsgrove",
    "State College",
    "Stroudsburg",
    "Wilkes-Barre"
]

# Common folder categories in your structure (from analysis)
FOLDER_CATEGORIES = {
    "sales": ["Sales Presentations", "B2B Selling", "Media Kits", "Sales Packages", "Rate Cards", "Proposal Templates"],
    "marketing": ["Packages", "Promotions", "Wall of Wisdom", "Sales Forms"],
    "resources": ["Market Resources", "Quarterly Seminar Materials", "Training", "Templates", "Streaming Resources"],
    "creative": ["Creative", "Logos", "Letterhead", "Postcards"],
    "coverage": ["Coverage Maps", "Rate Card", "Rate Cards"],
    "campaigns": ["Christmas", "Veteran's Day", "Half Price Hookup", "Comedy Club"],
    "education": ["Wall of Wisdom", "Wizard of Ads", "eBooks", "Training Pieces"]
}

# Time patterns to recognize
TIME_PATTERNS = {
    "years": r"20\d{2}",  # Matches 2021, 2022, 2025, etc.
    "quarters": r"Q[1-4]",
    "months": r"(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
    "seasons": r"(Spring|Summer|Fall|Winter|Holiday|Christmas)"
}

# Query expansion templates for your structure
MARKET_QUERY_EXPANSIONS = {
    "markets": "markets regions territories areas locations {market_list}",
    "packages": "packages programs offerings deals promotions",
    "presentations": "presentations pitches decks slides proposals",
    "resources": "resources materials documents guides training",
    "campaigns": "campaigns promotions events programs initiatives"
}

# Folder path abbreviations (for natural language)
FOLDER_ALIASES = {
    "wall of wisdom": ["WOW", "wall", "wisdom", "training materials"],
    "b2b": ["B2B", "business to business", "business selling"],
    "media kit": ["media kits", "kits", "marketing materials"],
    "packages": ["packages", "programs", "offerings"],
    "promotions": ["promos", "promotions", "campaigns"]
}

# Priority folders for quick access
PRIORITY_FOLDERS = [
    "2025",  # Current year content
    "2026",  # Future planning
    "Media Kits",
    "Sales Presentations",
    "Packages"
]
