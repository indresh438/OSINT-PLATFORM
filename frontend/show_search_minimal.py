def show_search():
    """Show search interface - Hacker themed"""
    st.markdown("## 🔍 INTELLIGENCE SEARCH TERMINAL")
    st.markdown("### Execute deep web reconnaissance")
    
    # Search form with cyber styling
    with st.form("search_form"):
        st.markdown("#### 🎯 TARGET PARAMETERS")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "🔎 SEARCH QUERY",
                placeholder="⚡ email | IP | domain | username | phone | hash...",
                help="Enter target identifier for reconnaissance"
            )
        
        with col2:
            limit = st.number_input("📊 MAX RESULTS", min_value=10, max_value=1000, value=100)
        
        st.markdown("---")
        st.markdown("#### ⚙️ FILTER CONFIGURATION")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            entity_types = st.multiselect(
                "🎯 TARGET TYPE",
                ["email", "ip", "domain", "username", "phone", "hash", "url", "btc_address"],
                default=None,
                help="Filter by specific intelligence type"
            )
        
        with col2:
            deduplicate = st.checkbox(
                "🧹 DEDUPLICATE",
                value=True,
                help="Remove duplicate entries"
            )
        
        # Auto-exclude noise tables
        exclude_tables = ["notifications", "logs", "sessions", "audit", "cache", "tokens"] if deduplicate else None
        exclude_sources_input = None
        
        st.markdown("---")
        submit = st.form_submit_button("⚡ INITIATE SEARCH", use_container_width=True)
    
    # Execute search with loading animation
    if submit and query:
        # Parse exclusion lists
        exclude_sources = [s.strip() for s in exclude_sources_input.split(",")] if exclude_sources_input else None
        exclude_sources = [s for s in exclude_sources if s] if exclude_sources else None
        
        with st.spinner("🔄 Scanning intelligence databases..."):
            results = search_entities(
                query, 
                entity_types or None, 
                limit,
                deduplicate=deduplicate,
                exclude_tables=exclude_tables,
                exclude_sources=exclude_sources
            )
        
        if results:
            total = results.get("total", 0)
            entities = results.get("results", [])
            took = results.get("took", 0)
            
            # Cyber-themed header
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #00ff41 0%, #00d9ff 100%); 
                        padding: 15px 20px; border-radius: 6px; margin-bottom: 20px; 
                        border: 2px solid #00ff41; box-shadow: 0 0 20px rgba(0,255,65,0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 28px; font-weight: bold; color: #000; font-family: 'Fira Code', monospace;">{total}</div>
                        <div style="color: #0a0e27; font-size: 13px; font-family: 'Fira Code', monospace;">⚡ FOUND IN {took:.2f}s</div>
                    </div>
                    <div>
                        {'<span style="background: rgba(0,0,0,0.3); padding: 5px 12px; border-radius: 12px; font-size: 11px; color: #000; font-weight: 600;">✨ UNIQUE</span>' if deduplicate else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if entities:
                # Group results by source (database)
                leaks_by_source = {}
                for entity in entities:
                    source = entity.get('source', 'Unknown Source')
                    if source not in leaks_by_source:
                        leaks_by_source[source] = []
                    leaks_by_source[source].append(entity)
                
                # Display each database
                for source_idx, (source, source_entities) in enumerate(leaks_by_source.items(), 1):
                    num_records = len(source_entities)
                    
                    # Database header - Cyber style
                    st.markdown(f"""
                    <div style="background: linear-gradient(90deg, #0f1419 0%, #1a1a2e 100%); 
                                padding: 10px 15px; border-radius: 4px; 
                                margin: 15px 0 10px 0; border-left: 4px solid #00ff41;
                                box-shadow: 0 0 10px rgba(0,255,65,0.2);">
                        <strong style="color: #00ff41; font-family: 'Fira Code', monospace;">
                            🗄️ DATABASE {source_idx}: {source.upper()}
                        </strong>
                        <span style="color: #00d9ff; font-size: 12px; margin-left: 8px; font-family: 'Fira Code', monospace;">
                            ({num_records} RECORDS)
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display records
                    for idx, entity in enumerate(source_entities, 1):
                        duplicate_count = entity.get('duplicate_count', 0)
                        
                        # Build info line
                        info_parts = []
                        if entity.get('email'):
                            info_parts.append(f"📧 {entity['email']}")
                        if entity.get('username'):
                            info_parts.append(f"👤 {entity['username']}")
                        if entity.get('phone'):
                            info_parts.append(f"📱 {entity['phone']}")
                        if entity.get('ip'):
                            info_parts.append(f"🖥️ {entity['ip']}")
                        if entity.get('domain'):
                            info_parts.append(f"🌍 {entity['domain']}")
                        
                        dup_text = f" <span style='color: #fa5252;'>(+{duplicate_count-1} more)</span>" if duplicate_count > 1 else ""
                        info_text = ' • '.join(info_parts) if info_parts else "No additional info"
                        
                        st.markdown(f"""
                        <div style="background: white; padding: 10px; border-radius: 4px; 
                                    margin-bottom: 8px; border: 1px solid #dee2e6; font-size: 13px;">
                            <strong style="color: #667eea;">{entity.get('value', 'N/A')}</strong>{dup_text}
                            <br><small style="color: #6c757d;">{info_text}</small>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No results found")
        else:
            st.error("Search failed. Please check backend connection.")
