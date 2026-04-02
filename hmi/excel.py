import xlsxwriter, os
from datetime import datetime
from pathlib import Path

def get_time():
    return str(datetime.now().strftime("%Y-%m-%d %H_%M_%S"))

def save_data(data, filename):
    # get parent home directory
    parent_dir = str(Path.home()) + "/Desktop/"
    # check if directory exists
    if not os.path.exists(parent_dir + '/mixer_data_recordings'):
        os.makedirs(parent_dir + '/mixer_data_recordings')
    file_path_name = ''
    if filename == '':
        file_path_name = "mixer_test" + '-' + get_time() + '.xlsx'
    else:
        file_path_name = filename + '-' + get_time() + '.xlsx'
    workbook = xlsxwriter.Workbook(file_path_name)    # Create an new Excel file and add a worksheet.
    worksheet = workbook.add_worksheet()

    # Widen the first column to make the text clearer.
    worksheet.set_column('A:A', 20)
    worksheet.set_column('B:B', 20)
    worksheet.set_column('C:C', 20)
    worksheet.set_column('D:D', 20)
    worksheet.set_column('E:E', 20)
    worksheet.set_column('F:F', 20)
    worksheet.set_column('G:G', 20)
    worksheet.set_column('H:H', 20)
    worksheet.set_column('I:I', 20)
    worksheet.set_column('J:J', 20)
    worksheet.set_column('K:K', 20)
    worksheet.set_column('L:L', 20)
    worksheet.set_column('M:M', 20)
    worksheet.set_column('N:N', 20)
    worksheet.set_column('O:O', 20)
    worksheet.set_column('P:P', 20)
    worksheet.set_column('Q:Q', 20)

    # Add a bold format to use to highlight cells.
    header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'align': 'center', 'valign': 'vcenter'})

    # Write some simple text.
    worksheet.write('A1', 'Start Time', header_format)
    worksheet.write('B1', 'Stop Time', header_format)
    worksheet.write('C1', 'Elapsed Time', header_format)
    worksheet.write('D1', 'Time Stamps', header_format) # on each line of measurement (1 second each recording)
    worksheet.write('E1', 'RPM', header_format)
    worksheet.write('F1', 'Torque', header_format)
    worksheet.write('G1', 'Blade Tip Velocity', header_format)
    worksheet.write('H1', 'Total Revolution', header_format)
    worksheet.write('I1', 'Notes', header_format)
    worksheet.write('J1', 'Weight', header_format)
    worksheet.write('K1', 'Feeder Total Mass', header_format)
    worksheet.write('L1', 'Feeder Weight', header_format)
    worksheet.write('M1', 'Feeder Mass Flow', header_format)
    worksheet.write('N1', 'Feeder Motor Velocity', header_format)
    worksheet.write('O1', 'Feeder Motor Current', header_format)
    worksheet.write('P1', 'Feeder State', header_format)
    worksheet.write('Q1', 'Feeder Mode', header_format)

    # write data dictionary into excel 
    row = 1
    col = 0
    # write each value tuple index into excel
    for key, value in data.items():
        for i in range(len(value)):
            if len(value) > 0:  # if there is data in the list
                worksheet.write(row, col, value[i]) # write the value into the excel
            row += 1
            
        row = 1
        col += 1

    workbook.close()
    
