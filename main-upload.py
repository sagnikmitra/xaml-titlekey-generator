import streamlit as st
import os
from io import BytesIO
import zipfile
import datetime
import pytz

st.set_page_config(layout="wide")

def detect_titles(xaml_content, file_name):
    titles = []
    new_xaml_content = ""
    lines_with_titles = []
    property_name = None
    for i, line in enumerate(xaml_content.split('\n'), start=1):
        if ' Title="' in line:
            title_start = line.index(' Title="') + len(' Title="')
            title_end = line.index('"', title_start)
            title = line[title_start:title_end]
            titles.append(title)
            property_name = get_property_name(line)
            new_line = replace_title_with_titlekey(line, file_name, property_name, title_end, title_start)
            lines_with_titles.append((i, title, new_line, title_start))
            new_xaml_content += new_line + "\n"
        else:
            new_xaml_content += line + "\n"
    return lines_with_titles, new_xaml_content, titles

def get_property_name(line):
    if ' Property="' in line:
        property_start = line.index(' Property="') + len(' Property="')
        property_end = line.index('"', property_start)
        return line[property_start:property_end]
    elif ' TextProperty="' in line:
        text_property_start = line.index(' TextProperty="') + len(' TextProperty="')
        text_property_end = line.index('"', text_property_start)
        return line[text_property_start:text_property_end]
    elif ' Name="' in line:
        name_property_start = line.index(' Name="') + len(' Name="')
        name_property_end = line.index('"', name_property_start)
        return line[name_property_start:name_property_end]
    elif ' Group="' in line:
        group_property_start = line.index(' Group="') + len(' Group="')
        group_property_end = line.index('"', group_property_start)
        return line[group_property_start:group_property_end]
    else:
        old_title_start = line.index(' Title="') + len(' Title="')
        old_title_end = line.index('"', old_title_start)
        old_title = line[old_title_start:old_title_end]
        return old_title.replace(" ", "")


def replace_title_with_titlekey(line, file_name, property_name, title_end, title_start):
    if 'Title="' in line:
        if property_name:
            new_line = line.replace('Title="', f'TitleKey="{file_name}.{property_name}.Title"')
        else:
            new_line = line.replace('Title="', f'TitleKey="{file_name}.Text.Title"')
        end_index = new_line.index('"', new_line.index('TitleKey="') + len('TitleKey="'))
        new_line = new_line[:end_index] + new_line[end_index + (title_end-title_start+1):]    
        return new_line
    else:
        return line


def generate_text_resource(lines_with_titles):
    text_resource_lines = set()  
    for line_number, title, line_content, _ in lines_with_titles:
        title_key = line_content.split('TitleKey="')[1].split('"')[0]
        text_resource_line = f'<TextResource Name="{title_key}" Value="{title}"/>'
        text_resource_lines.add(text_resource_line)
    return text_resource_lines


def process_xaml_content(xaml_content, file_name, if_mode_of_input_entry):
    lines_with_titles, new_xaml_content, all_titles = detect_titles(xaml_content, file_name)
    if(if_mode_of_input_entry):
        st.subheader("Modified XAML Content:")
        st.code(new_xaml_content, language='xml')
        st.subheader("Generated Text Resource:")
        
    text_resource_lines = generate_text_resource(lines_with_titles)
    sorted_text_resource_lines = sorted(text_resource_lines) 
    xml_text = '\n'.join(sorted_text_resource_lines)
    
    if(if_mode_of_input_entry):
        st.code(xml_text, language='xml')
        st.subheader("Lines with the generated Title Keys:")
    
    table_data = []
    table_data.append(('Line Number', 'Old Title', 'New Title Key', 'Line Content Updated'))

    for line_number, title, new_line_content, _ in lines_with_titles:
        new_title_key = new_line_content.split('TitleKey="')[1].split('"')[0]
        table_data.append((line_number, title, new_title_key, new_line_content))

    if(if_mode_of_input_entry):   
        st.table(table_data)

    return all_titles, text_resource_lines, table_data


st.title("XAML Title Detector")

option = st.radio("Choose an option:", ("Upload File", "Enter File Content and Name"))

if option == "Upload File":
    uploaded_files = st.file_uploader("Upload XAML Files", type=["xaml"], accept_multiple_files=True)

    if uploaded_files:
        all_files = []
        all_text_resources = set()
        all_table_data = []

        for uploaded_file in uploaded_files:
            file_name = os.path.splitext(uploaded_file.name)[0] 
            xaml_content = uploaded_file.getvalue().decode("utf-8") 

            st.info(f"Processed {file_name}")
            titles, text_resources, table_data = process_xaml_content(xaml_content, file_name, False)
            
            all_files.append((file_name, xaml_content))
            all_text_resources.update(text_resources)
            all_table_data.extend(table_data)

        if st.button("Download All Updated Files"):
            zip_file = BytesIO()
            file_name_string = ""
            with zipfile.ZipFile(zip_file, 'w') as zipf:
                for file_name, content in all_files:
                    updated_file_content = detect_titles(content, file_name)[1]
                    zipf.writestr(f"{file_name}.xaml", updated_file_content.encode())
                    file_name_string += "_" + file_name
            zip_file.seek(0)
            ist = pytz.timezone('Asia/Kolkata')
            current_datetime = datetime.datetime.now(ist).strftime("%d%m%Y_%H%M%S")
            zip_filename = f"Processed_XAML_Files_{current_datetime}{file_name_string}.zip"
            st.download_button(label="Download", data=zip_file, file_name=zip_filename, mime="application/zip")
            
        st.subheader("Collated Text Resources:")
        collated_xml_text = '\n'.join(all_text_resources)
        st.code(collated_xml_text, language='xml')

        st.subheader("Collated Table Data:")
        st.dataframe(all_table_data)


elif option == "Enter File Content and Name":
    file_name = st.text_input("Enter File Name (without extension)")

    xaml_content = st.text_area("Paste your XAML content here")

    if st.button("Detect Titles"):
        process_xaml_content(xaml_content, file_name, True)
