import sys
import json
import os
import uuid

def generate_plot(data_str):
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd
        
        # Parse data
        emotions = json.loads(data_str)
        # emotions looks like {'Angry': 10, 'Happy': 50, ...}
        
        df = pd.DataFrame(list(emotions.items()), columns=['Emotion', 'Intensity'])
        
        # Setup seaborn
        sns.set_theme(style="darkgrid")
        plt.figure(figsize=(8, 6))
        
        # Create bar plot
        ax = sns.barplot(x='Emotion', y='Intensity', data=df, palette='viridis')
        plt.title('Session Emotion Distribution (Seaborn)', fontsize=16, color='white')
        plt.xticks(rotation=45, color='white')
        plt.yticks(color='white')
        
        # Adjust background for dark mode UI
        ax.set_facecolor('#1e293b')
        ax.figure.set_facecolor('#0f172a')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        
        # Save plot
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'reports')
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"seaborn_report_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(output_dir, filename)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(json.dumps({"success": True, "filename": filename}))
        
    except ImportError as e:
        print(json.dumps({"success": False, "error": f"Missing library: {e}. Please 'pip install seaborn matplotlib pandas'"}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    # Read from stdin
    input_data = sys.stdin.read()
    if input_data:
        generate_plot(input_data)
    else:
        print(json.dumps({"success": False, "error": "No data provided"}))
