#!/usr/bin/env python3
"""
Run PropertyEngine enrichment workflow on both AUCTIONS_MASTER and POTENTIAL_TRADES
"""

from run_listing_enrichment_workflow import ListingEnrichmentWorkflow

def main():
    """Run the PropertyEngine enrichment workflow"""
    
    print("🚀 Starting PropertyEngine Enrichment Workflow")
    print("=" * 60)
    print("This will:")
    print("1. Scan both AUCTIONS_MASTER and POTENTIAL_TRADES sheets")
    print("2. Find rows missing guide_price or source_url")
    print("3. Use PropertyEngine to enrich them with guide prices and URLs")
    print("4. Update the existing rows directly (no add+delete)")
    print("=" * 60)
    
    try:
        # Initialize the workflow
        workflow = ListingEnrichmentWorkflow()
        
        # Run the complete workflow
        workflow.run_workflow()
        
        print("\n🎉 PropertyEngine enrichment workflow completed!")
        
    except Exception as e:
        print(f"\n❌ Error running PropertyEngine enrichment workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 