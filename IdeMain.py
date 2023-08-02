import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

class CodeEditor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the font to Courier New
        font = QFont()
        font.setFamily("Courier New")
        font.setFixedPitch(True)
        font.setPointSize(10)
        self.setFont(font)
        self.setMarginsFont(font)

        # Margin 0 is used for line numbers
        fontmetrics = QFontMetrics(font)
        self.setMarginsFont(font)
        self.setMarginWidth(0, fontmetrics.width("00000") + 6)
        self.setMarginLineNumbers(0, True)
        self.setMarginsBackgroundColor(QColor("#cccccc"))

        # Brace matching: enable for a brace immediately before or after the current position
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#ffe4e4"))

        # Set Python lexer
        lexer = QsciLexerPython()
        lexer.setDefaultFont(font)
        self.setLexer(lexer)

        # Auto indentation
        self.setAutoIndent(True)

        # Set tab width
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)

        # Autocompletion
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setAutoCompletionThreshold(1)

        # Folding margin
        self.setFolding(QsciScintilla.BoxedTreeFoldStyle)

        # Disable command key
        self.SendScintilla(QsciScintilla.SCI_CLEARCMDKEY, ord('D')+ (ord('U')<<16))
        self.SendScintilla(QsciScintilla.SCI_CLEARCMDKEY, ord('D')+ (ord('D')<<16))

        # Multiline editing
        self.SendScintilla(QsciScintilla.SCI_SETMULTIPASTE, 1)
        self.SendScintilla(QsciScintilla.SCI_SETADDITIONALSELECTIONTYPING, 1)

class TerminalEmulator(QWidget):
    def __init__(self):
        super(TerminalEmulator, self).__init__()

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.start('cmd.exe')
        self.terminal = QTextEdit(self)
        self.terminal.setReadOnly(True)
        self.command_line = CommandLineEdit(self)
        self.command_line.returnPressed.connect(self.execute_command)

        layout = QVBoxLayout(self)
        layout.addWidget(self.terminal)
        layout.addWidget(self.command_line)

        self.process.readyRead.connect(self.update_terminal)
        self.process.finished.connect(self.process_finished)

        self.update_prompt()

    def execute_command(self):
        command = self.command_line.text()
        self.command_line.add_to_history(command)
        if command.strip() == 'cls':
            self.terminal.clear()
        else:
            self.terminal.append(command)
            self.process.write((command + '\n').encode())
        self.command_line.clear()

    def update_terminal(self):
        output = self.process.readAll().data().decode(errors='ignore')
        self.terminal.append(output)

    def process_finished(self):
        self.terminal.append("Process finished.")
        self.update_prompt()

    def update_prompt(self):
        self.command_line.setPlaceholderText('>')

class CommandLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super(CommandLineEdit, self).__init__(*args, **kwargs)
        self.history = []
        self.history_index = 0

    def add_to_history(self, command):
        self.history.append(command)
        self.history_index = len(self.history)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up and self.history:
            self.history_index = max(0, self.history_index - 1)
            self.setText(self.history[self.history_index])
        elif event.key() == Qt.Key_Down and self.history:
            self.history_index = min(len(self.history) - 1, self.history_index + 1)
            self.setText(self.history[self.history_index])
        else:
            super(CommandLineEdit, self).keyPressEvent(event)

class IDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(800, 600)

        self.filenames = []
        self.editors = []
        self.current_index = 0

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.change_tab)

        self.terminal = TerminalEmulator()

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.terminal.update_terminal)

        self.file_tree = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_tree.setModel(self.file_model)
        self.file_tree.clicked.connect(self.open_file_from_tree)

        self.file_tree.hide()

        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(self.file_tree)
        splitter1.addWidget(self.tab_widget)
        splitter1.setSizes([100, 900])

        splitter2 = QSplitter(Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(self.terminal)
        splitter2.setSizes([350, 100])

        self.setCentralWidget(splitter2)

        toolbar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        toolbar.addAction(new_action)

        open_action = QAction("Open", self)
        open_action.setShortcut("Ctrl+O")
        toolbar.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        toolbar.addAction(save_action)

        open_folder_action = QAction("Open Folder", self)
        toolbar.addAction(open_folder_action)

        new_action.triggered.connect(self.new_file)
        open_action.triggered.connect(self.open_file)
        save_action.triggered.connect(self.save_file)
        open_folder_action.triggered.connect(self.open_folder)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_code)
        self.run_button.setStyleSheet("""
            border: 1px solid #d3d3d3;
            border-radius: 5px;
            padding: 5px;
            margin-left: 5px;
            background-color: #4caf50;
            color: white;
        """)

        self.compile_button = QPushButton("Compile")
        self.compile_button.clicked.connect(self.compile_code)
        self.compile_button.setStyleSheet("""
            border: 1px solid #d3d3d3;
            border-radius: 5px;
            padding: 5px;
            margin-left: 5px;
            background-color: #4caf50;
            color: white;
        """)
        self.compile_button.setShortcut(QKeySequence("Ctrl+K"))

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self.run_button)
        toolbar.addWidget(self.compile_button)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Dark', 'Light'])

        # Find the width of the longest string
        max_width = 0
        for i in range(self.theme_combo.count()):
            width = QFontMetrics(self.theme_combo.font()).width(self.theme_combo.itemText(i))
            max_width = max(max_width, width)

        # Set the width of the QComboBox
        self.theme_combo.setMinimumWidth(max_width + 50)  # Add some padding

        self.theme_combo.currentTextChanged.connect(self.change_theme)
        toolbar.addWidget(self.theme_combo)


        self.setWindowTitle("Simple IDE")
        self.show()

        # Load settings
        self.settings = QSettings('YourOrganization', 'YourApplication')
        last_file = self.settings.value('last_file', '', type=str)  # Define last_file with a default value
        last_dir = self.settings.value('last_dir', '', type=str)  # Define last_dir with a default value
        last_theme = self.settings.value('last_theme', 'Light', type=str)  # Define last_theme with a default value
        self.theme_combo.setCurrentText(last_theme)
        self.change_theme(last_theme)
        self.open_last_folder(last_dir)
        self.load_last_opened_files()

    def open_last_folder(self,last_dir):
        if os.path.isdir(last_dir):
            self.file_model.setRootPath(last_dir)
            self.file_tree.setRootIndex(self.file_model.index(last_dir))
            self.file_tree.show()
    
    def load_last_opened_files(self):
        last_files = self.settings.value('last_files', [], type=list)
        for file_path in last_files:
            self.open_file_by_name(file_path)


    def new_file(self):
        editor = CodeEditor()
        editor.setFont(QFont('Courier', 12))
        self.editors.append(editor)
        self.filenames.append(None)
        self.tab_widget.addTab(editor, "Untitled")
        self.tab_widget.setCurrentIndex(len(self.editors) - 1)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File")
        if filename:
            self.open_file_by_name(filename)
            self.settings.setValue('last_file', filename)  # Save last file

    def open_file_by_name(self, filename):
        with open(filename, 'r', errors='ignore') as f:
            text = f.read()
        editor = CodeEditor()
        editor.setFont(QFont('Courier', 12))
        editor.setText(text)
        self.editors.append(editor)
        self.filenames.append(filename)
        self.tab_widget.addTab(editor, filename.split('/')[-1])
        self.tab_widget.setCurrentIndex(len(self.editors) - 1)



    def open_file_from_tree(self, index):
        filename = self.file_model.filePath(index)
        if os.path.isfile(filename):
            self.open_file_by_name(filename)

    def open_folder(self):
        if not self.is_file_saved(self.tab_widget.currentIndex()):
            response = QMessageBox.question(self, "Save Changes?", "Do you want to save changes to the current file before opening a new folder?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if response == QMessageBox.Save:
                self.save_file()
            elif response == QMessageBox.Cancel:
                return
        foldername = QFileDialog.getExistingDirectory(self, "Open Folder")
        if foldername:
            self.file_model.setRootPath(foldername)
            self.file_tree.setRootIndex(self.file_model.index(foldername))
            self.file_tree.show()
            self.settings.setValue('last_dir', foldername)  # Save last directory


    def save_file(self):
        index = self.tab_widget.currentIndex()
        if index == -1:  # No open file
            return
        filename = self.filenames[index]
        if filename is None:
            filename, _ = QFileDialog.getSaveFileName(self, "Save File")
            if filename:  # Check if filename is not empty
                self.filenames[index] = filename
        if filename:
            text = self.editors[index].text()
            with open(filename, 'w') as f:
                f.write(text)
            self.settings.setValue('last_file', filename)  # Save last file



    def close_tab(self, index):
        self.tab_widget.removeTab(index)
        del self.editors[index]
        del self.filenames[index]

    def change_tab(self, index):
        if index >= 0:
            filename = self.filenames[index]
            self.setWindowTitle(filename if filename else "IDEO")
            # Fade-in animation
            self.animation = QPropertyAnimation(self.tab_widget.widget(index), b"windowOpacity")
            self.animation.setDuration(1000)
            self.animation.setStartValue(0)
            self.animation.setEndValue(1)
            self.animation.setEasingCurve(QEasingCurve.InOutQuad)
            self.animation.start()

    def compile_code(self):
        index = self.tab_widget.currentIndex()
        filename = self.filenames[index]
        code = self.editors[index].text()

        if not self.is_file_saved(index) or filename is None:
            QMessageBox.warning(self, "File Not Saved", "Please save the file before compiling.")
            return

        if filename.endswith('.py'):
            file_name = os.path.basename(filename) if filename else 'code.py'
            with open(filename, 'w') as f:
                f.write(code)
            self.terminal.process.write(f'python -m py_compile {filename}\n'.encode())

        elif filename.endswith('.cpp'):
            file_name = os.path.basename(filename) if filename else 'code.cpp'
            with open(filename, 'w') as f:
                f.write(code)
            executable_name = os.path.splitext(filename)[0]
            self.terminal.process.write(f'g++ {filename} -o {executable_name}\n'.encode())

        elif filename.endswith('.java'):
            file_name = os.path.basename(filename) if filename else 'Main.java'
            with open(filename, 'w') as f:
                f.write(code)
            self.terminal.process.write(f'javac {filename}\n'.encode())

        elif filename.endswith('.c'):
            file_name = os.path.basename(filename) if filename else 'code.c'
            with open(filename, 'w') as f:
                f.write(code)
            executable_name = os.path.splitext(filename)[0]
            self.terminal.process.write(f'gcc {filename} -o {executable_name}\n'.encode())

    def run_code(self):
        index = self.tab_widget.currentIndex()
        filename = self.filenames[index]
        code = self.editors[index].text()

        if not self.is_file_saved(index) or filename is None:
            QMessageBox.warning(self, "File Not Saved", "Please save the file before compiling.")
            return

        if filename.endswith('.py'):
            file_name = os.path.basename(filename) if filename else 'code.py'
            with open(filename, 'w') as f:
                f.write(code)
            self.terminal.process.write(f'python {filename}\n'.encode())

        elif filename.endswith('.cpp'):
            file_name = os.path.basename(filename) if filename else 'code.cpp'
            with open(filename, 'w') as f:
                f.write(code)
            executable_name = os.path.splitext(filename)[0]
            self.terminal.process.write(f'{executable_name}\n'.encode())

        elif filename.endswith('.java'):
            file_name = os.path.basename(filename) if filename else 'Main.java'
            with open(filename, 'w') as f:
                f.write(code)
            class_name = os.path.splitext(file_name)[0]
            file_location = os.path.dirname(filename)
            self.terminal.process.write(f'javac -d {file_location} {filename} && java -cp {file_location} {class_name}\n'.encode())

        elif filename.endswith('.c'):
            file_name = os.path.basename(filename) if filename else 'code.c'
            with open(filename, 'w') as f:
                f.write(code)
            executable_name = os.path.splitext(filename)[0]
            self.terminal.process.write(f'gcc {filename} -o {executable_name} && start {executable_name}\n'.encode())

    def keyPressEvent(self, event):
        if self.process.state() == QProcess.Running:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self.process.write(bytes('\n', 'utf-8'))
                self.terminal.terminal.append('\n')
            else:
                self.process.write(bytes(event.text(), 'utf-8'))
        else:
            super().keyPressEvent(event)

    def close_tab(self, index):
        if not self.is_file_saved(index):
            response = QMessageBox.question(self, "Save Changes?", "Do you want to save changes to this file before closing?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if response == QMessageBox.Save:
                self.save_file()
            elif response == QMessageBox.Cancel:
                return
        self.tab_widget.removeTab(index)
        del self.editors[index]
        del self.filenames[index]

    def is_file_saved(self, index):
        if index >= 0 and index < len(self.filenames):
            if self.filenames[index] is None:
                return not bool(self.editors[index].text())
            with open(self.filenames[index], 'r', encoding='utf-8', errors='ignore') as f:
                return f.read() == self.editors[index].text()
        return True  # Return True if index is out of range


    def closeEvent(self, event):
        if not self.is_file_saved(self.tab_widget.currentIndex()):
            response = QMessageBox.question(self, "Save Changes?", "Do you want to save changes to the current file before closing the application?", QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if response == QMessageBox.Save:
                self.save_file()
            elif response == QMessageBox.Cancel:
                event.ignore()
                return
        # Save settings when the application is about to close
        self.settings.sync()
        last_files = [filename for filename in self.filenames if filename is not None]
        self.settings.setValue('last_files', last_files)
        self.settings.sync()
        super().closeEvent(event)

    def load_theme(self, css_file):
        with open(css_file, "r") as f:
            self.setStyleSheet(f.read())

    def change_theme(self, theme):
        if theme == 'Dark':
            self.load_theme('C:/Users/root/Desktop/Project/Editor/dark.css')
        elif theme == 'Light':
            self.load_theme('C:/Users/root/Desktop/Project/Editor/light.css')
        self.settings.setValue('last_theme', theme)  # Save last theme


app = QApplication(sys.argv)
app.setStyle('Fusion')
ide = IDE()
sys.exit(app.exec_())