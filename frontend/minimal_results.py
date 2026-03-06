# Cyber-themed results display code for app.py

# Replace the entire results section with this:

            if entities:
                # Group results by source (database)
                leaks_by_source = {}
                for entity in entities:
                    source = entity.get('source', 'Unknown Source')
                    if source not in leaks_by_source:
                        leaks_by_source[source] = []
                    leaks_by_source[source].append(entity)
                
                # Display each database with hacker design
                for source_idx, (source, source_entities) in enumerate(leaks_by_source.items(), 1):
                    num_records = len(source_entities)
                    
                    # Cyber-themed database header
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
                        
                        # Build info line with cyber icons
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
                        
                        dup_text = f" <span style='color: #ff006e; font-weight: 600;'>[+{duplicate_count-1} duplicates]</span>" if duplicate_count > 1 else ""
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #0f1419 0%, #1a1a2e 100%); 
                                    padding: 12px 15px; border-radius: 4px; 
                                    margin-bottom: 8px; border: 1px solid #00ff41; 
                                    font-size: 13px; font-family: 'Fira Code', monospace;
                                    box-shadow: 0 0 5px rgba(0,255,65,0.1);
                                    transition: all 0.3s;">
                            <strong style="color: #00d9ff; font-size: 14px;">⚡ {entity.get('value', 'N/A')}</strong>
                            {dup_text}
                            <br><small style="color: #00ff41; opacity: 0.8;">{' • '.join(info_parts)}</small>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No intelligence data found")

