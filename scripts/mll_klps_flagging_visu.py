# %%
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd


# %%
def generate_colored_html(df, klps_list, output_file):
    """
    Generates an HTML file with sentences, where flagged sentences are colorized.

    Parameters:
    sentences (list of str): The list of sentences.
    flagged_indices (list of int): The indices of the sentences to flag.
    output_file (str): The output HTML file name.

    Returns:
    None
    """
    # Define colors for flagged sentences
    #colors = ['red', 'green', 'orange', 'dodgerblue', 'magenta']  # Choose CSS color names
    colors = ['#FF6F61', '#2E8B57', '#FFA500', '#1E90FF', '#FF69B4']

    # Create the opening HTML tags
    #html_content = '<html>\n<head><title>Colored Sentences</title></head>\n<body>\n'
    html_content = '''<html>
    <head>
        <title>Colored Sentences</title>
        <style>
            body { background-color: black; color: white; }
        </style>
    </head>
    <body>'''

    html_content += f'<p>Key Learning points:</p>\n'

    for i, klp in enumerate(klps_list):
        html_content += f'<p style="color: {colors[i]};">{klp}</p>\n'

    html_content += f'<p>-----------------\n</p><p>Transcript:</p>\n'
    
    # Iterate through sentences and apply color to flagged ones
    for _, row in df.iterrows():
        #if pd.notna(row["klp assigned idx"]):
        if row["klp assigned idx"] != 0:
            # Pick a color based on the index (cycling through the colors list)
            color = colors[int(row['klp assigned idx'])-1 % len(colors)]
        #    html_content += f'<p style="color: {color};">{row['transcript sentence']}</p>\n'
        #else:
        #    html_content += f'<p>{row['transcript sentence']}</p>\n'
            html_content += f'<span style="color: {color};">{row["transcript sentence"]}</span> '
        else:
            html_content += f'<span>{row["transcript sentence"]}</span> '
    
    # Add closing HTML tags
    html_content += '</body></html>'

    # Write the HTML content to the specified file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"HTML file '{output_file}' created successfully!")


# %%
def generate_colored_html_3(df, klps_list, klp_to_color, output_file):
    """
    Generates an HTML file with sentences, where flagged sentences are colorized, 
    and includes a title and surrounding boxes for the key learning points and the transcript.

    Parameters:
    df (DataFrame): The DataFrame containing sentences and assigned flags.
    klps_list (list of str): The list of Key Learning Points (KLPs).
    output_file (str): The output HTML file name.

    Returns:
    None
    """
    # Define modern color palette for flagged sentences
    colors = ['#FF6F61', '#2E8B57', '#FFA500', '#1E90FF', '#FF69B4']

    # Create the opening HTML with CSS styling for the background, block, and text color
    html_content = '''
    <html>
    <head>
        <title>Colored Sentences Visualization</title>
        <style>
            body { background-color: #121212; color: white; font-family: Arial, sans-serif; padding: 20px; }
            .content { max-width: 2000px; margin: auto; }
            h1 { text-align: center; color: white; margin-bottom: 30px; }  /* Title in white */
            
            /* General styling for boxes */
            .box {
                background-color: #282828; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
                border: 1px solid grey; /* Grey border for the boxes */
            }

            /* Key Learning Points box */
            .klp-box {
                border-left: 5px solid rgba(255, 255, 255, 0.2); 
                margin-bottom: 20px;
                padding-left: 15px;
                max-width: 1100px; /* Make the transcript box wider */
                margin: 0 auto;  /* Center the box */
                /*text-align: center; /* Center text within box */
            }
            
            /* Transcript box with wider width */
            .transcript-box {
                border-left: 5px solid rgba(255, 255, 255, 0.2);
                padding-left: 15px;
                max-width: 2000px; /* Make the transcript box wider */
                margin: 0 auto;
            }
            
            .klp { font-size: 1.1em; font-weight: bold; } 
            p { line-height: 1.6; margin-bottom: 10px; }
            hr { border: none; border-top: 1px solid #444; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="content">
            <h1>Lesson</h1>
            
            <div class="box klp-box">
                <h2>Key Learning Points</h2>
    '''

    # Add Key Learning Points with colors and "KLP Number:"
    for i, klp in enumerate(klps_list):
        klp_number = i + 1  # KLP Number
        html_content += f'<p class="klp" style="color: {colors[i]};">KLP {klp_number}: {klp}</p>\n'

    html_content += '''
            </div>
            <hr>
            <div class="box transcript-box">
                <h2>Transcript</h2>
    '''

    # Iterate through sentences and apply color to flagged ones
    for _, row in df.iterrows():
        #if row["klp assigned idx"] != 0:  # If it's flagged, color it
        if row["klp assigned idx"] == klp_to_color:
            color = colors[int(row['klp assigned idx'])-1 % len(colors)]
            html_content += f'<span style="color: {color};">{row["transcript sentence"]}</span>'
        else:
            html_content += f'<span>{row["transcript sentence"]}</span> '
    
    # Close the HTML content
    html_content += '''
            </div>
        </div>
    </body>
    </html>
    '''

    # Write the HTML content to the specified file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"HTML file '{output_file}' created successfully!")


def generate_colored_html_5(df, klps_list, output_file):
    """
    Generates an HTML file with sentences, where flagged sentences are colorized, 
    and includes a title and surrounding boxes for the key learning points and the transcript.

    Parameters:
    df (DataFrame): The DataFrame containing sentences and assigned flags.
    klps_list (list of str): The list of Key Learning Points (KLPs).
    output_file (str): The output HTML file name.

    Returns:
    None
    """
    # Define modern color palette for flagged sentences
    colors = ['#FF6F61', '#2E8B57', '#FFA500', '#1E90FF', '#FF69B4']

    # Create the opening HTML with CSS styling for the background, block, and text color
    html_content = '''
    <html>
    <head>
        <title>Colored Sentences Visualization</title>
        <style>
            body { background-color: #121212; color: white; font-family: Arial, sans-serif; padding: 20px; }
            .content { max-width: 2000px; margin: auto; }
            h1 { text-align: center; color: white; margin-bottom: 30px; }  /* Title in white */
            
            /* General styling for boxes */
            .box {
                background-color: #282828; 
                padding: 20px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
                border: 1px solid grey; /* Grey border for the boxes */
            }

            /* Key Learning Points box */
            .klp-box {
                border-left: 5px solid rgba(255, 255, 255, 0.2); 
                margin-bottom: 20px;
                padding-left: 15px;
                max-width: 1100px; /* Make the transcript box wider */
                margin: 0 auto;  /* Center the box */
            }
            
            /* Transcript box with wider width */
            .transcript-box {
                border-left: 5px solid rgba(255, 255, 255, 0.2);
                padding-left: 15px;
                max-width: 2000px; /* Make the transcript box wider */
                margin: 0 auto;
            }
            
            .klp { font-size: 1.1em; font-weight: bold; } 
            p { line-height: 1.6; margin-bottom: 10px; }
            hr { border: none; border-top: 1px solid #444; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="content">
            <h1>Lesson</h1>
            
            <div class="box klp-box">
                <h2>Key Learning Points</h2>
    '''

    # Add Key Learning Points with colors and "KLP Number:"
    for i, klp in enumerate(klps_list):
        klp_number = i + 1  # KLP Number
        html_content += f'<p class="klp" style="color: {colors[i]};">KLP {klp_number}: {klp}</p>\n'

    html_content += '''
            </div>
            <hr>
            <div class="box transcript-box">
                <h2>Transcript</h2>
    '''

    # Initialize variables to track color and character count
    last_color = None
    character_count = 0
    unflagged_character_count = 0  # Count for unflagged sentences
    unflagged_color = None  # Track color for unflagged sentences

    # Iterate through sentences and apply color to flagged ones
    for _, row in df.iterrows():
        if row["klp assigned idx"] != 0:  # If it's flagged, color it
            color = colors[int(row['klp assigned idx']) - 1 % len(colors)]
            # Check if the color is the same as the last one
            if color == last_color:
                # Check character count and limit to 100 if necessary
                if character_count < 800:
                    html_content += f'<span style="color: {color};">{row["transcript sentence"]}</span>'
                    character_count += len(row["transcript sentence"])
            else:
                # Reset for new color and start over with the new color
                last_color = color
                character_count = len(row["transcript sentence"])
                html_content += f'<span style="color: {color};">{row["transcript sentence"]}</span>'
        else:
            # Handle unflagged sentences
            if unflagged_color is None:
                unflagged_color = 'default'  # Track unflagged color as a unique identifier
                unflagged_character_count = len(row["transcript sentence"])
                html_content += f'<span>{row["transcript sentence"]}</span> '
            else:
                # Check character count for unflagged sentences
                if unflagged_character_count < 800:
                    html_content += f'<span>{row["transcript sentence"]}</span> '
                    unflagged_character_count += len(row["transcript sentence"])

    # Close the HTML content
    html_content += '''
            </div>
        </div>
    </body>
    </html>
    '''

    # Write the HTML content to the specified file
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"HTML file '{output_file}' created successfully!")


