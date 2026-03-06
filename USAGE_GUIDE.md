# 🔍 OSINT Platform - Complete Usage Guide

## 📌 Quick Access

**Website URL**: http://localhost:8501  
**API Documentation**: http://localhost:8000/docs  
**Neo4j Browser**: http://localhost:7474

---

## 🚀 Getting Started

### Step 1: Access the Platform
Open your web browser and go to:
```
http://localhost:8501
```

### Step 2: Check System Status
The dashboard will show:
- ✅ All services online/offline
- 📊 Total records indexed
- 🔢 Number of entities found

---

## 🔍 HOW TO SEARCH

### What You Can Search For

| Type | Example | Description |
|------|---------|-------------|
| **Email** | `john@gmail.com` | Find email addresses |
| **Username** | `admin` or `john_doe` | Find user accounts |
| **IP Address** | `192.168.1.1` | Find IP addresses |
| **Phone** | `9876543210` | Find phone numbers |
| **Domain** | `example.com` | Find domains |
| **URL** | `https://site.com` | Find URLs |
| **Hash** | `5d41402abc4b...` | Find hashes (MD5/SHA) |

---

## 📝 Search Examples

### Basic Searches

#### 1. Search for Specific Email
```
john@gmail.com
```

#### 2. Find All Gmail Addresses
```
@gmail.com
```

#### 3. Search for Username
```
admin
```
or
```
john_doe
```

#### 4. Find IP Address
```
192.168.1.1
```

#### 5. Find All IPs in Range
```
192.168
```

#### 6. Search for Phone Number
```
9876543210
```

#### 7. Search for Domain
```
example.com
```

#### 8. Partial Searches
```
john          → finds emails/usernames containing "john"
@yahoo        → finds all Yahoo emails
+91           → finds Indian phone numbers
192.          → finds all IPs starting with 192
```

---

## ⚙️ Search Configuration

### 1. MAX RESULTS
- Set between **10** to **1000**
- Default: **100**
- Controls how many results to display

### 2. TARGET TYPE Filter
Choose specific types to search:
- ✅ email
- ✅ ip
- ✅ domain
- ✅ username
- ✅ phone
- ✅ hash
- ✅ url
- ✅ btc_address

**Leave empty** to search ALL types

### 3. DEDUPLICATE
- ✅ **Checked** (Recommended): Removes duplicate entries
- ⬜ **Unchecked**: Shows all matches including duplicates

---

## 📊 Understanding Search Results

### Results Display

When you search, you'll see:

```
╔════════════════════════════════════════╗
║  123  found in 0.45s         ✓ Unique ║
╚════════════════════════════════════════╝

💾 Database Name
   45 records
   
   ▼ EMAIL: john@example.com  (+2)
     📧 john@example.com
     👤 john_doe
     📱 9876543210
     🖥️ 192.168.1.100
     🌍 example.com
     Additional Data:
       name: John Doe
       city: Mumbai
       created: 2023-05-15
```

### Result Components

1. **Total Count**: Number of matches found
2. **Search Time**: How fast the search completed
3. **Unique Badge**: Shows if deduplication is active
4. **Database Groups**: Results organized by source database
5. **Record Count**: Number of records per database
6. **Expandable Details**: Click to see full information

### Icons Meaning

| Icon | Meaning |
|------|---------|
| 📧 | Email address |
| 👤 | Username |
| 📱 | Phone number |
| 🖥️ | IP address |
| 🌍 | Domain |
| 🔗 | URL |
| 💾 | Source database |
| (+2) | Duplicate count |

---

## 🎯 Advanced Search Tips

### 1. Broad Searches
Start with broad searches to see what data you have:
```
@gmail.com        → All Gmail users
admin             → All admin accounts
192.168           → All local IPs
test              → All test accounts
```

### 2. Specific Searches
Once you know what exists, search specifically:
```
admin@company.com
john.doe@gmail.com
192.168.1.100
```

### 3. Domain Analysis
Find all users from a specific domain:
```
@company.com      → All company emails
@yahoo.com        → All Yahoo emails
```

### 4. IP Range Analysis
Find all IPs in a subnet:
```
192.168.1.        → IPs from 192.168.1.0-255
10.0.             → IPs from 10.0.x.x
```

### 5. Pattern Matching
Search for patterns:
```
admin             → admin, administrator, admin123
test              → test, testing, test_user
```

---

## 📥 Import Data Tab

### How to Import MySQL Dumps

1. Go to **📥 Import Data** tab
2. Fill in the form:
   - **Source Name**: Give it a name (e.g., "login_system")
   - **Dump File**: Path to your .sql file in `/dumps/`
   - **Field Mapping**: Specify which columns contain emails, IPs, etc.

3. Click **🚀 Start Import**
4. Monitor progress in real-time

### Example Field Mapping
```json
{
  "users": {
    "email_column": "email",
    "username_column": "username",
    "ip_column": "registration_ip",
    "phone_column": "mobile"
  },
  "login_logs": {
    "email_column": "user_email",
    "ip_column": "login_ip"
  }
}
```

---

## 📊 Statistics Tab

View analytics about your data:

### Available Statistics
- **Total Entities**: Count by type (emails, IPs, domains, etc.)
- **Distribution Charts**: Visual breakdown
- **Database Statistics**: Records per source
- **Top Domains**: Most common email domains
- **Top IPs**: Most frequent IP addresses

---

## 🔧 Troubleshooting

### No Results Found?
1. Check if data is imported (Statistics tab)
2. Try broader search terms
3. Remove filters (TARGET TYPE)
4. Check spelling

### Search Too Slow?
1. Reduce MAX RESULTS
2. Use more specific search terms
3. Apply TARGET TYPE filters
4. Enable DEDUPLICATE

### Can't Access Website?
```bash
# Check if services are running
sudo docker ps | grep osint

# Restart services
cd /home/indeed/Desktop/local_osint
sudo docker-compose restart
```

---

## 💡 Best Practices

### 1. Start Simple
- Begin with common searches like `@gmail.com`
- Get familiar with the interface
- Understand your data

### 2. Use Filters
- Apply TARGET TYPE for specific searches
- Always enable DEDUPLICATE for cleaner results
- Start with 100 results, increase if needed

### 3. Expand Results
- Click each result to see full details
- Check metadata for additional information
- Note the source database for context

### 4. Organize Your Searches
- Search by domain to group users
- Search by IP range to find networks
- Search by patterns to find similar accounts

### 5. Export Results
- Take screenshots of important findings
- Copy data from expanded results
- Use API for bulk exports (advanced)

---

## 🎓 Common Search Scenarios

### Scenario 1: Find All User Accounts
```
Search: admin
Filter: username
Result: All admin accounts across databases
```

### Scenario 2: Investigate an Email
```
Search: suspicious@example.com
Filter: (none)
Result: All data related to that email
```

### Scenario 3: Map IP Address Activity
```
Search: 192.168.1.100
Filter: ip
Result: All records with that IP
```

### Scenario 4: Domain Intelligence
```
Search: @company.com
Filter: email
Result: All employees/users from that company
```

### Scenario 5: Phone Number Lookup
```
Search: 9876543210
Filter: phone
Result: All accounts with that phone number
```

---

## 🔐 Privacy & Security Notes

- All data stays on your local machine
- No internet connection required
- Access only via localhost (not accessible remotely)
- Secure your system with proper permissions
- Back up your data regularly

---

## 📞 Quick Reference Commands

### Start Platform
```bash
cd /home/indeed/Desktop/local_osint
./start.sh
```

### Stop Platform
```bash
./stop.sh
```

### Check Status
```bash
./status.sh
```

### View Logs
```bash
sudo docker logs osint_backend
sudo docker logs osint_frontend
```

---

## 🎯 Summary

**To search:**
1. Go to http://localhost:8501
2. Enter search term in SEARCH QUERY box
3. (Optional) Select filters
4. Click INITIATE SEARCH
5. Expand results to see details

**Search is case-insensitive and supports partial matches!**

Happy investigating! 🔍
