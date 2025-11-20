import subprocess
from pathlib import Path


def generate_report():
    """Generate analysis report using event_report.py"""
    print("\n" + "="*60)
    print("GENERATING REPORT...")
    print("="*60 + "\n")
    
    try:
        import event_report
        _, report_path = event_report.run_analysis_with_report()
        return report_path
    except Exception as e:
        print(f"\n✗ Error generating report: {e}")
        return None


def render_report(report_path):
    """Render the Quarto report"""
    print("\nChoose output format:")
    print("  1. PDF with medstata-typst (default)")
    print("  2. HTML")
    format_choice = input("Enter choice (1 or 2): ").strip()
    
    print(f"\nRendering report...")
    print("-"*60)
    
    try:
        if format_choice == "2":
            # For HTML, explicitly specify the format
            result = subprocess.run(
                ["quarto", "render", str(report_path), "--to", "html"],
                capture_output=True,
                text=True
            )
            output_format = "html"
            output_file = report_path.parent / f"{report_path.stem}.html"
        else:
            # For PDF with medstata-typst, don't specify --to, let it use the YAML default
            result = subprocess.run(
                ["quarto", "render", str(report_path)],
                capture_output=True,
                text=True
            )
            output_format = "pdf"
            output_file = report_path.parent / f"{report_path.stem}.pdf"
        
        if result.returncode == 0:
            print(f"\n✓ Report successfully rendered to {output_format.upper()}!")
            print(f"  Output: {output_file}")
        else:
            print(f"\n✗ Error rendering report:")
            print(result.stderr)
            
    except FileNotFoundError:
        print(f"\n✗ Error: Quarto not found")
        print(f"  Install from: https://quarto.org/docs/get-started/")
    except Exception as e:
        print(f"\n✗ Error: {e}")


def main():
    """Main workflow orchestrator"""
    print("\n" + "="*60)
    print("OpenFDA MEDICAL DEVICE ANALYSIS TOOL")
    print("="*60)
    
    # Step 1: Run search
    import search
    database, original_query, n_results, last_updated = search.main()
    
    # Check if search was successful
    if database is None:
        print("\n" + "="*60)
        print("PROCESS COMPLETE")
        print("="*60 + "\n")
        return
    
    # Step 2: Offer report generation for event database
    if database == 'event':
        print("\n" + "-"*60)
        print("REPORT GENERATION")
        print("-"*60)
        report_choice = input("\nWould you like to generate an analysis report? (y/n): ").strip().lower()
        
        if report_choice == 'y':
            report_path = generate_report()
            
            if report_path:
                render_choice = input("\nWould you like to render the report now? (y/n): ").strip().lower()
                
                if render_choice == 'y':
                    render_report(report_path)
        else:
            print("\nSkipping report generation.")
    
    print("\n" + "="*60)
    print("PROCESS COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()