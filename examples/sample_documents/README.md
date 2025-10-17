# Sample Documents

This directory contains sample documents for testing the Agentic RAG system.

## Documents

1. **research_paper.txt** - A sample research paper about machine learning and NLP
   - Topics: Machine learning, NLP, BERT, transformer models
   - Contains: Methodology, results, future work
   - Good for: Testing technical queries, accuracy metrics, methodology questions

2. **api_guide.txt** - API integration documentation
   - Topics: REST API, authentication, endpoints, rate limits
   - Contains: Technical specifications, best practices
   - Good for: Testing procedural queries, how-to questions

3. **quarterly_report.txt** - Business performance report
   - Topics: Revenue, growth metrics, market expansion
   - Contains: Financial data, KPIs, challenges, outlook
   - Good for: Testing business intelligence queries, metric extraction

## Usage

### Upload All Documents

```bash
# From the project root
cd examples/sample_documents

# Upload each document
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@research_paper.txt"

curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@api_guide.txt"

curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@quarterly_report.txt"
```

### Upload Script

```bash
#!/bin/bash
# upload_samples.sh

for file in *.txt; do
    echo "Uploading $file..."
    curl -X POST http://localhost:8000/api/documents/upload \
      -F "file=@$file"
    echo ""
done

echo "All documents uploaded!"
```

Make it executable and run:
```bash
chmod +x upload_samples.sh
./upload_samples.sh
```

## Example Queries

After uploading these documents, try these queries:

### Research Paper Queries
- "What accuracy did the model achieve?"
- "What methodologies were used?"
- "What are the future work directions?"
- "How does the new model compare to the baseline?"

### API Guide Queries
- "How do I authenticate with the API?"
- "What are the rate limits?"
- "What endpoints are available?"
- "What should I do if I get a 429 error?"

### Business Report Queries
- "What was the Q3 revenue?"
- "How many new customers were acquired?"
- "What challenges did the company face?"
- "What are the Q4 projections?"

### Cross-Document Queries
- "Compare the technical improvements in the research with the business results"
- "What API features would support the Q4 mobile app initiative?"
- "How do the processing time improvements relate to customer satisfaction?"

## Creating Your Own Test Documents

To create effective test documents:

1. **Use Clear Structure:** Include headings, sections, and lists
2. **Include Metrics:** Numbers, percentages, and specific data points
3. **Add Context:** Background information and explanations
4. **Vary Content:** Mix technical, business, and procedural information
5. **Use Keywords:** Include terms users might search for

## Document Formats

The system supports:
- `.txt` - Plain text (like these samples)
- `.pdf` - PDF documents
- `.docx` - Microsoft Word documents
- `.hwp` - Korean Hangul Word Processor
- `.hwpx` - Korean Hangul XML format

Convert these samples to other formats for testing:

```bash
# Convert to PDF (requires pandoc)
pandoc research_paper.txt -o research_paper.pdf

# Convert to DOCX
pandoc research_paper.txt -o research_paper.docx
```
