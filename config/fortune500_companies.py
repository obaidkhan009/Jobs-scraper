"""
Fortune 500 Company Lists for Job Scraping.

Contains companies organized by the job platform they use (Greenhouse, Lever, Workday).
These lists are used by the async scrapers for parallel job fetching.
"""

# ============================================================================
# GREENHOUSE COMPANIES (API: boards-api.greenhouse.io)
# Format: (company_slug, display_name)
# ============================================================================

GREENHOUSE_FORTUNE_500 = [
    # === TECHNOLOGY (FAANG & Big Tech) ===
    ("apple", "Apple"),
    ("meta", "Meta"),
    ("amazon", "Amazon"),
    ("netflix", "Netflix"),
    ("google", "Google"),
    ("microsoft", "Microsoft"),
    ("nvidia", "NVIDIA"),
    ("intel", "Intel"),
    ("amd", "AMD"),
    ("qualcomm", "Qualcomm"),
    ("broadcom", "Broadcom"),
    ("cisco", "Cisco"),
    ("oracle", "Oracle"),
    ("ibm", "IBM"),
    ("dell", "Dell Technologies"),
    ("hp", "HP Inc"),
    ("hpe", "Hewlett Packard Enterprise"),
    ("salesforce", "Salesforce"),
    ("adobe", "Adobe"),
    ("vmware", "VMware"),
    ("servicenow", "ServiceNow"),
    ("workday", "Workday"),
    ("splunk", "Splunk"),
    ("paloaltonetworks", "Palo Alto Networks"),
    ("crowdstrike", "CrowdStrike"),
    ("fortinet", "Fortinet"),
    ("zscaler", "Zscaler"),
    ("okta", "Okta"),
    ("datadog", "Datadog"),
    ("snowflake", "Snowflake"),
    ("mongodb", "MongoDB"),
    ("elastic", "Elastic"),
    ("confluent", "Confluent"),
    ("hashicorp", "HashiCorp"),
    ("twilio", "Twilio"),
    ("zendesk", "Zendesk"),
    ("hubspot", "HubSpot"),
    ("atlassian", "Atlassian"),
    ("docusign", "DocuSign"),
    ("dropbox", "Dropbox"),
    ("box", "Box"),
    ("zoom", "Zoom"),
    ("ringcentral", "RingCentral"),
    
    # === AI/ML COMPANIES ===
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("deepmind", "DeepMind"),
    ("cohere", "Cohere"),
    ("scale", "Scale AI"),
    ("huggingface", "Hugging Face"),
    ("databricks", "Databricks"),
    ("weights-and-biases", "Weights & Biases"),
    ("anyscale", "Anyscale"),
    ("runwayml", "Runway"),
    ("midjourney", "Midjourney"),
    ("jasperai", "Jasper AI"),
    ("replicate", "Replicate"),
    ("together", "Together AI"),
    ("mosaic", "MosaicML"),
    ("langchain", "LangChain"),
    ("pinecone", "Pinecone"),
    ("weaviate", "Weaviate"),
    
    # === FINTECH & PAYMENTS ===
    ("stripe", "Stripe"),
    ("square", "Block (Square)"),
    ("paypal", "PayPal"),
    ("visa", "Visa"),
    ("mastercard", "Mastercard"),
    ("americanexpress", "American Express"),
    ("discover", "Discover"),
    ("capitalone", "Capital One"),
    ("jpmorgan", "JPMorgan Chase"),
    ("goldmansachs", "Goldman Sachs"),
    ("morganstanley", "Morgan Stanley"),
    ("bankofamerica", "Bank of America"),
    ("wellsfargo", "Wells Fargo"),
    ("citigroup", "Citigroup"),
    ("usbank", "US Bank"),
    ("pnc", "PNC"),
    ("truist", "Truist"),
    ("coinbase", "Coinbase"),
    ("robinhood", "Robinhood"),
    ("sofi", "SoFi"),
    ("chime", "Chime"),
    ("plaid", "Plaid"),
    ("brex", "Brex"),
    ("ramp", "Ramp"),
    ("affirm", "Affirm"),
    ("klarna", "Klarna"),
    
    # === E-COMMERCE & RETAIL ===
    ("shopify", "Shopify"),
    ("ebay", "eBay"),
    ("etsy", "Etsy"),
    ("wayfair", "Wayfair"),
    ("chewy", "Chewy"),
    ("instacart", "Instacart"),
    ("doordash", "DoorDash"),
    ("uber", "Uber"),
    ("lyft", "Lyft"),
    ("airbnb", "Airbnb"),
    ("booking", "Booking.com"),
    ("expedia", "Expedia"),
    ("tripadvisor", "TripAdvisor"),
    
    # === MEDIA & ENTERTAINMENT ===
    ("spotify", "Spotify"),
    ("discord", "Discord"),
    ("twitch", "Twitch"),
    ("roblox", "Roblox"),
    ("unity", "Unity"),
    ("epicgames", "Epic Games"),
    ("ea", "Electronic Arts"),
    ("activision", "Activision Blizzard"),
    ("take2", "Take-Two Interactive"),
    ("warner", "Warner Bros Discovery"),
    ("paramount", "Paramount"),
    ("disney", "Disney"),
    ("nbcuniversal", "NBCUniversal"),
    ("fox", "Fox Corporation"),
    
    # === SOCIAL & COMMUNICATION ===
    ("snap", "Snap"),
    ("pinterest", "Pinterest"),
    ("reddit", "Reddit"),
    ("twitter", "X (Twitter)"),
    ("linkedin", "LinkedIn"),
    ("slack", "Slack"),
    ("notion", "Notion"),
    ("figma", "Figma"),
    ("canva", "Canva"),
    ("miro", "Miro"),
    
    # === CLOUD & INFRASTRUCTURE ===
    ("cloudflare", "Cloudflare"),
    ("digitalocean", "DigitalOcean"),
    ("linode", "Linode"),
    ("vercel", "Vercel"),
    ("netlify", "Netlify"),
    ("heroku", "Heroku"),
    ("render", "Render"),
    ("railway", "Railway"),
    ("fly", "Fly.io"),
    ("supabase", "Supabase"),
    ("planetscale", "PlanetScale"),
    ("cockroachlabs", "Cockroach Labs"),
    ("timescale", "Timescale"),
    
    # === HEALTHCARE & BIOTECH ===
    ("unitedhealth", "UnitedHealth Group"),
    ("cvs", "CVS Health"),
    ("cigna", "Cigna"),
    ("anthem", "Elevance Health"),
    ("humana", "Humana"),
    ("centene", "Centene"),
    ("molina", "Molina Healthcare"),
    ("oscar", "Oscar Health"),
    ("clover", "Clover Health"),
    ("veeva", "Veeva Systems"),
    ("tempus", "Tempus"),
    ("flatiron", "Flatiron Health"),
    ("grail", "GRAIL"),
    
    # === AUTOMOTIVE & TRANSPORTATION ===
    ("tesla", "Tesla"),
    ("rivian", "Rivian"),
    ("lucid", "Lucid Motors"),
    ("gm", "General Motors"),
    ("ford", "Ford"),
    ("toyota", "Toyota"),
    ("waymo", "Waymo"),
    ("cruise", "Cruise"),
    ("aurora", "Aurora"),
    ("nuro", "Nuro"),
    ("zoox", "Zoox"),
    
    # === AEROSPACE & DEFENSE ===
    ("spacex", "SpaceX"),
    ("blueorigin", "Blue Origin"),
    ("lockheedmartin", "Lockheed Martin"),
    ("northropgrumman", "Northrop Grumman"),
    ("raytheon", "RTX (Raytheon)"),
    ("boeing", "Boeing"),
    ("generalatomics", "General Atomics"),
    ("anduril", "Anduril"),
    ("palantir", "Palantir"),
    
    # === CONSULTING & PROFESSIONAL SERVICES ===
    ("accenture", "Accenture"),
    ("deloitte", "Deloitte"),
    ("pwc", "PwC"),
    ("ey", "Ernst & Young"),
    ("kpmg", "KPMG"),
    ("mckinsey", "McKinsey"),
    ("bcg", "Boston Consulting Group"),
    ("bain", "Bain & Company"),
    
    # === TELECOM ===
    ("att", "AT&T"),
    ("verizon", "Verizon"),
    ("tmobile", "T-Mobile"),
    ("comcast", "Comcast"),
    ("charter", "Charter Communications"),
    
    # === ENERGY ===
    ("exxon", "ExxonMobil"),
    ("chevron", "Chevron"),
    ("conocophillips", "ConocoPhillips"),
    ("nextera", "NextEra Energy"),
    ("duke", "Duke Energy"),
    ("southern", "Southern Company"),
    
    # === UNICORNS & HIGH-GROWTH STARTUPS ===
    ("flexport", "Flexport"),
    ("loom", "Loom"),
    ("webflow", "Webflow"),
    ("deel", "Deel"),
    ("retool", "Retool"),
    ("postman", "Postman"),
    ("airtable", "Airtable"),
    ("amplitude", "Amplitude"),
    ("segment", "Segment"),
    ("mixpanel", "Mixpanel"),
    ("heap", "Heap"),
    ("fullstory", "FullStory"),
    ("launchdarkly", "LaunchDarkly"),
    ("linear", "Linear"),
    ("loom", "Loom"),
    ("ashby", "Ashby"),
    ("rippling", "Rippling"),
    ("gusto", "Gusto"),
    ("lattice", "Lattice"),
    ("lever", "Lever"),
    ("greenhouse", "Greenhouse"),
    ("gem", "Gem"),
    ("ashby", "Ashby"),
]

# ============================================================================
# LEVER COMPANIES (API: jobs.lever.co)
# Format: (company_slug, display_name)
# ============================================================================

LEVER_FORTUNE_500 = [
    # === BIG TECH ===
    ("netflix", "Netflix"),
    ("shopify", "Shopify"),
    ("lyft", "Lyft"),
    ("twitch", "Twitch"),
    ("roblox", "Roblox"),
    ("unity", "Unity"),
    ("robinhood", "Robinhood"),
    ("affirm", "Affirm"),
    ("opendoor", "Opendoor"),
    
    # === AI & ML ===
    ("perplexity", "Perplexity"),
    ("character", "Character.AI"),
    ("stability", "Stability AI"),
    ("adept", "Adept"),
    ("inflection", "Inflection AI"),
    ("covariant", "Covariant"),
    ("standard", "Standard AI"),
    
    # === TECH COMPANIES ===
    ("flexport", "Flexport"),
    ("loom", "Loom"),
    ("webflow", "Webflow"),
    ("deel", "Deel"),
    ("retool", "Retool"),
    ("postman", "Postman"),
    ("miro", "Miro"),
    ("airtable", "Airtable"),
    ("amplitude", "Amplitude"),
    ("carta", "Carta"),
    ("brex", "Brex"),
    ("plaid", "Plaid"),
    ("chime", "Chime"),
    ("mercury", "Mercury"),
    ("ramp", "Ramp"),
    
    # === CLOUD/INFRA ===
    ("tailscale", "Tailscale"),
    ("vercel", "Vercel"),
    ("supabase", "Supabase"),
    ("planetscale", "PlanetScale"),
    ("railway", "Railway"),
    ("render", "Render"),
    ("fly", "Fly.io"),
    ("neon", "Neon"),
    
    # === DEVTOOLS ===
    ("linear", "Linear"),
    ("raycast", "Raycast"),
    ("fig", "Fig"),
    ("warp", "Warp"),
    ("cursor", "Cursor"),
    ("replit", "Replit"),
    ("gitpod", "Gitpod"),
    ("codespaces", "GitHub Codespaces"),
    
    # === SECURITY ===
    ("1password", "1Password"),
    ("snyk", "Snyk"),
    ("lacework", "Lacework"),
    ("orca", "Orca Security"),
    ("wiz", "Wiz"),
    ("tessian", "Tessian"),
    
    # === HR & PEOPLE ===
    ("rippling", "Rippling"),
    ("gusto", "Gusto"),
    ("lattice", "Lattice"),
    ("lever", "Lever"),
    ("ashby", "Ashby"),
    ("gem", "Gem"),
    ("greenhouse", "Greenhouse"),
    ("checkr", "Checkr"),
    
    # === FINTECH ===
    ("stripe", "Stripe"),
    ("square", "Block"),
    ("coinbase", "Coinbase"),
    ("kraken", "Kraken"),
    ("gemini", "Gemini"),
    ("opensea", "OpenSea"),
    ("dapper", "Dapper Labs"),
    ("alchemy", "Alchemy"),
    
    # === HEALTHCARE ===
    ("ro", "Ro"),
    ("cityblock", "Cityblock Health"),
    ("forward", "Forward"),
    ("color", "Color"),
    ("cerebral", "Cerebral"),
    
    # === E-COMMERCE ===
    ("faire", "Faire"),
    ("goat", "GOAT"),
    ("poshmark", "Poshmark"),
    ("whatnot", "Whatnot"),
    ("fanatics", "Fanatics"),
]

# Count totals
TOTAL_GREENHOUSE = len(GREENHOUSE_FORTUNE_500)
TOTAL_LEVER = len(LEVER_FORTUNE_500)
TOTAL_COMPANIES = TOTAL_GREENHOUSE + TOTAL_LEVER

print(f"[Company Lists] Loaded {TOTAL_GREENHOUSE} Greenhouse + {TOTAL_LEVER} Lever = {TOTAL_COMPANIES} total companies")
