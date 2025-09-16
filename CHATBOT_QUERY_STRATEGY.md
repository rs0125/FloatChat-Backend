# 🤖 Chatbot Query Management Strategy

## 📋 Overview

With ingestion routes removed (handled by external data pipeline), here's how chatbot queries will be managed using both the original `/api/query` and the new `/api/semantic/query/optimized` routes.

## 🚀 **Recommended Chatbot Architecture**

### **Option 1: Single Optimized Endpoint (RECOMMENDED)**

```python
# Frontend Chatbot Implementation
async function handleUserQuery(userQuery) {
    try {
        const response = await fetch('/api/semantic/query/optimized', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: userQuery,
                strategy: 'adaptive'  // Let the system decide
            })
        });
        
        const result = await response.json();
        return formatChatbotResponse(result);
    } catch (error) {
        console.error('Query failed:', error);
        return "Sorry, I couldn't process your query right now.";
    }
}
```

**Benefits:**
- ✅ Automatically chooses best approach (SQL vs Vector vs Hybrid)
- ✅ Built-in performance monitoring and fallback
- ✅ Single endpoint to maintain
- ✅ Adaptive learning from query patterns

---

### **Option 2: Dual Route with Intelligent Routing**

```python
# Frontend Chatbot with Query Classification
async function handleUserQuery(userQuery) {
    const queryType = classifyQuery(userQuery);
    
    switch(queryType) {
        case 'STRUCTURED_SQL':
            // Use original SQL-only route for complex data queries
            return await querySQL(userQuery);
            
        case 'SEMANTIC_SEARCH':
            // Use vector search for descriptive queries
            return await queryVector(userQuery);
            
        case 'HYBRID':
        default:
            // Use optimized route for everything else
            return await queryOptimized(userQuery);
    }
}

async function querySQL(userQuery) {
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userQuery })
    });
    return response.json();
}

async function queryOptimized(userQuery) {
    const response = await fetch('/api/semantic/query/optimized', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: userQuery,
            strategy: 'adaptive'
        })
    });
    return response.json();
}

function classifyQuery(query) {
    const lowerQuery = query.toLowerCase();
    
    // SQL-optimized patterns
    if (lowerQuery.includes('show me all') || 
        lowerQuery.includes('list all') ||
        lowerQuery.includes('count') ||
        lowerQuery.includes('average') ||
        lowerQuery.includes('group by')) {
        return 'STRUCTURED_SQL';
    }
    
    // Vector-optimized patterns  
    if (lowerQuery.includes('similar to') ||
        lowerQuery.includes('like') ||
        lowerQuery.includes('describe') ||
        lowerQuery.includes('find floats for')) {
        return 'SEMANTIC_SEARCH';
    }
    
    return 'HYBRID';
}
```

---

## 🔄 **Query Flow Comparison**

### **Original Route: `/api/query`**
```
User Query → LangChain Agent → SQL Generation → Supabase → Response
```

**Best For:**
- Complex SQL aggregations
- Precise numeric/date filters
- Multi-table joins
- Statistical analysis

**Examples:**
- "Show me all floats deployed in 2023"
- "What's the average temperature at 100m depth?"
- "Count floats by region"

### **Optimized Route: `/api/semantic/query/optimized`**
```
User Query → Classification → Route Selection → Best Database → Response
                ↓
    [SQL Database] ← Adaptive Router → [Vector Database]
                ↓
         Performance Monitoring + Fallback
```

**Best For:**
- Natural language queries
- Semantic similarity
- Mixed query types
- Automatic optimization

**Examples:**
- "Find deep ocean research floats"
- "Floats measuring temperature in Arctic waters"
- "Similar floats to the ones studying climate change"

---

## 🎯 **Deployment Strategies**

### **Strategy A: Gradual Migration**

```python
# Phase 1: Use both routes based on user intent
async function chatbotHandler(userQuery, useOptimized = false) {
    if (useOptimized || isComplexSemanticQuery(userQuery)) {
        return await queryOptimized(userQuery);
    } else {
        // Fallback to original route
        try {
            return await querySQL(userQuery);
        } catch (error) {
            // Auto-fallback to optimized route
            return await queryOptimized(userQuery);
        }
    }
}

// Phase 2: Monitor performance and gradually shift traffic
// Phase 3: Eventually use only optimized route
```

### **Strategy B: A/B Testing**

```python
async function chatbotHandler(userQuery) {
    const userSegment = getUserSegment(); // A or B
    
    if (userSegment === 'A') {
        // Control group - original route
        return await querySQL(userQuery);
    } else {
        // Test group - optimized route
        return await queryOptimized(userQuery);
    }
}
```

### **Strategy C: Immediate Full Migration**

```python
// Use only the optimized route
async function chatbotHandler(userQuery) {
    return await fetch('/api/semantic/query/optimized', {
        method: 'POST',
        body: JSON.stringify({
            query: userQuery,
            strategy: 'adaptive'
        })
    });
}
```

---

## 🔧 **Configuration Options**

### **Query Strategies Available:**

1. **`adaptive`** (Recommended for chatbot)
   - Automatically learns and adapts
   - Best performance over time
   - Handles all query types

2. **`sql_first`**
   - Tries SQL first, falls back to vector
   - Good for data-heavy applications
   - Preserves SQL capabilities

3. **`vector_first`**
   - Semantic search priority
   - Best for research/discovery use cases
   - Fast similarity matching

4. **`concurrent`**
   - Runs both simultaneously
   - Best results but higher resource usage
   - Good for critical applications

---

## 📊 **Monitoring Integration**

```python
// Add query monitoring to chatbot
async function monitoredQuery(userQuery) {
    const startTime = Date.now();
    
    try {
        const result = await queryOptimized(userQuery);
        
        // Log successful query
        analytics.track('chatbot_query_success', {
            query: userQuery,
            responseTime: Date.now() - startTime,
            strategy: result.strategy_used,
            source: result.source
        });
        
        return result;
    } catch (error) {
        // Log failed query
        analytics.track('chatbot_query_failed', {
            query: userQuery,
            error: error.message,
            responseTime: Date.now() - startTime
        });
        
        throw error;
    }
}
```

---

## 🏆 **Final Recommendation**

**For your chatbot, I recommend using ONLY the optimized route:**

```javascript
// Simple, single-endpoint chatbot implementation
async function handleChatbotQuery(userMessage) {
    const response = await fetch('/api/semantic/query/optimized', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query: userMessage,
            strategy: 'adaptive'
        })
    });
    
    const result = await response.json();
    return formatForChatUI(result);
}
```

**Why?**
- ✅ Handles ALL query types automatically
- ✅ Learns and improves over time
- ✅ Built-in fallback mechanisms  
- ✅ Performance monitoring included
- ✅ Future-proof architecture
- ✅ Simpler to maintain

The original `/api/query` route can remain for backward compatibility or specific use cases, but the optimized route should be your primary chatbot interface.