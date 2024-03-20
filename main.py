import streamlit as st
st.set_page_config (layout="wide")
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
    return lines_with_titles, new_xaml_content

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
        return None

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
    text_resource_lines = set()  # Use a set to keep unique entries
    for line_number, title, line_content, _ in lines_with_titles:
        title_key = line_content.split('TitleKey="')[1].split('"')[0]
        text_resource_line = f'<TextResource Name="{title_key}" Value="{title}"/>'
        text_resource_lines.add(text_resource_line)
    return text_resource_lines

st.title("XAML Title Detector")

file_name = st.text_input("Enter File Name (without extension)")

xaml_content = st.text_area("Paste your XAML content here")

if st.button("Detect Titles"):
    lines_with_titles, new_xaml_content = detect_titles(xaml_content, file_name)

    st.subheader("Modified XAML Content:")
    st.code(new_xaml_content, language='xml')

    st.subheader("Generated Text Resource:")
    text_resource_lines = generate_text_resource(lines_with_titles)
    xml_text = '\n'.join(text_resource_lines)
    st.code(xml_text, language='xml')

    st.subheader("Lines with the generated Title Keys:")
    table_data = []
    table_data.append(('Line Number', 'Old Title', 'New Title Key', 'Line Content'))
    
    for line_number, title, new_line_content, _ in lines_with_titles: 
        new_title_key = new_line_content.split('TitleKey="')[1].split('"')[0]
        table_data.append((line_number, title, new_title_key, new_line_content))
    
    st.table(table_data)
