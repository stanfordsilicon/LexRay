# 🚀 CLDR Date Skeleton Converter - Quickstart Guide

## What Does This Program Do?

The **CLDR Date Skeleton Converter** is a tool that helps you understand how different languages format dates. It takes date expressions in English and their translations in other languages, then generates standardized formatting patterns called "CLDR skeletons."

**Real-world example:**
- **Input**: English "January 16, 2006" + Spanish "16 de enero de 2006"
- **Output**: 
  - English pattern: `MMMM d, y`
  - Spanish pattern: `d 'de' MMMM 'de' y`

These patterns can be used by software developers to properly format dates in different languages and cultures.

---

## 📋 Prerequisites

Before you start, make sure you have:
- A computer running Windows, Mac, or Linux
- Internet connection for downloading software
- About 30 minutes for setup

---

## 🛠️ Step 1: Install Required Software

### Install Python

1. **Go to** [python.org/downloads](https://python.org/downloads)
2. **Download** the latest Python version (3.8 or newer)
3. **Run the installer**
   - ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
   - ✅ Choose "Install for all users" if prompted
4. **Verify installation**:
   - Open Terminal (Mac) or Command Prompt (Windows)
   - Type: `python --version`
   - You should see something like `Python 3.11.5`

### Install Visual Studio Code (Optional but Recommended)

1. **Go to** [code.visualstudio.com](https://code.visualstudio.com)
2. **Download** VS Code for your operating system
3. **Install** with default settings
4. **Open** VS Code and install the Python extension:
   - Click the Extensions icon (puzzle piece) on the left sidebar
   - Search for "Python"
   - Install the official Python extension by Microsoft

---

## 📁 Step 2: Get the Program Files

### Option A: Download from GitHub (Easiest)
1. **Go to** the project repository (provided by your supervisor)
2. **Click** the green "Code" button
3. **Select** "Download ZIP"
4. **Extract** the ZIP file to your Desktop
5. **Rename** the folder to `LexRay` if needed

### Option B: Using Git (If you have it)
```bash
git clone [repository-url]
cd LexRay
```

---

## ⚙️ Step 3: Set Up the Program

### 1. Open Terminal/Command Prompt
- **Windows**: Press `Win + R`, type `cmd`, press Enter
- **Mac**: Press `Cmd + Space`, type "Terminal", press Enter
- **Linux**: Press `Ctrl + Alt + T`

### 2. Navigate to the Program Folder
```bash
cd Desktop/LexRay
```
*Adjust the path if you saved the files elsewhere*

### 3. Install Required Libraries
```bash
pip install pandas openpyxl regex
```
*This will download and install the necessary components*

### 4. Verify Setup
```bash
python cldr_converter.py
```
*You should see the program start with a welcome message*

---

## 📊 Step 4: Add Your Data Files

The program needs CLDR data files to work. These are Excel files containing date formatting information for different languages.

### File Structure
Your `cldr_data` folder should contain files like:
- `english_moderate.xlsx` (required)
- `spanish_moderate.xlsx`
- `french_moderate.xlsx`
- `german_moderate.xlsx`
- etc.

### Get the Data Files
1. **Ask your supervisor** for the CLDR data files
2. **Place them** in the `cldr_data` folder inside your LexRay directory
3. **Ensure** `english_moderate.xlsx` is present (this is required)

---

## 🎯 Step 5: Run the Program

### Starting the Program
1. **Open Terminal/Command Prompt**
2. **Navigate to LexRay folder**:
   ```bash
   cd Desktop/LexRay
   ```
3. **Run the program**:
   ```bash
   python cldr_converter.py
   ```

### Using the Program

The program will guide you through a conversation. Here's what to expect:

#### 1. **Set Data Path**
```
Default CLDR data path: /path/to/LexRay/cldr_data
Found 74 CLDR data files in default location.
Use default path? (yes/no, default: yes):
```
- **Type**: `yes` and press Enter

#### 2. **Enter English Date**
```
Enter an English date expression:
```
- **Type**: Any English date like `January 16, 2006` or `Aug 10, 2025`
- **Press**: Enter

#### 3. **View English Results**
The program will show you the English skeleton pattern:
```
CLDR skeleton for 'January 16, 2006': MMMM d, y
```

#### 4. **Add Translation (Optional)**
```
Do you have a translation of 'January 16, 2006' in a different language? (yes/no):
```
- **Type**: `yes` if you want to analyze a translation, `no` to finish

#### 5. **Choose Language**
```
Enter target language:
```
- **Type**: The language name like `spanish`, `french`, `german`
- The program will show available languages to help you

#### 6. **Enter Translation**
```
Enter the translation for 'January 16, 2006' in Spanish:
```
- **Type**: The translated date like `16 de enero de 2006`
- **Press**: Enter

#### 7. **View Results**
```
=== RESULTS ===
English skeleton for 'January 16, 2006': MMMM d, y
Spanish skeletons for '16 de enero de 2006': d 'de' MMMM 'de' y, dd 'de' MMMM 'de' y
```

---

## 📖 Understanding the Results

### Skeleton Patterns Explained
- **`MMMM`**: Full month name (January, febrero, août)
- **`MMM`**: Abbreviated month (Jan, feb, aoû)
- **`M`**: Narrow month (J, f, a)
- **`d`**: Day number (1, 2, 3...)
- **`dd`**: Zero-padded day (01, 02, 03...)
- **`y`**: Full year (2006, 2025)
- **`'de'`**: Literal text in quotes (words that aren't dates)

### Example Interpretations
- **`MMMM d, y`**: "January 16, 2006" format
- **`d 'de' MMMM 'de' y`**: "16 de enero de 2006" format
- **`MMM d–MMM d, y`**: "Aug 10–Sep 12, 2025" format

---

## 🔧 Troubleshooting Common Issues

### Problem: "Python is not recognized"
**Cause**: Python not installed or not in PATH
**Solution**: 
1. Reinstall Python from python.org
2. ✅ Check "Add Python to PATH" during installation
3. Restart your terminal/command prompt

### Problem: "No module named 'pandas'"
**Cause**: Required libraries not installed
**Solution**:
```bash
pip install pandas openpyxl regex
```

### Problem: "English reference file not found"
**Cause**: Missing `english_moderate.xlsx` file
**Solution**:
1. Check if `cldr_data/english_moderate.xlsx` exists
2. Ask your supervisor for the correct data files
3. Ensure the file is in the right location

### Problem: "Language not found"
**Cause**: Requested language data file doesn't exist
**Solution**:
1. Check available languages when the program lists them
2. Type the exact language name shown
3. Ensure the corresponding `.xlsx` file exists in `cldr_data`

### Problem: "Invalid translation" error
**Cause**: The translation doesn't match the expected pattern
**Solution**:
1. Double-check your translation for typos
2. Ensure you're translating the exact same date
3. Try a simpler date format first

### Problem: Program crashes or freezes
**Cause**: Various technical issues
**Solution**:
1. Press `Ctrl+C` to stop the program
2. Check if all required files are present
3. Restart the program with a simpler example
4. Contact your supervisor if the issue persists

### Problem: Strange characters in output
**Cause**: Terminal encoding issues
**Solution**:
1. Try using VS Code's integrated terminal
2. On Windows, try Windows Terminal instead of Command Prompt
3. Ensure your terminal supports Unicode characters

---

## 📞 Getting Help

If you encounter issues not covered in this guide:

1. **Check the file structure**: Ensure all files are in the right place
2. **Try a simple example**: Start with "January 1, 2025" in English
3. **Take screenshots**: Capture any error messages
4. **Contact your supervisor**: Provide details about what you were trying to do

---

## 💡 Tips for Success

- **Start simple**: Begin with basic dates like "January 1, 2025"
- **Check spelling**: Small typos can cause big problems
- **Use exact language names**: Type "spanish" not "Spanish" or "es"
- **Keep files organized**: Don't move or rename the program folders
- **Save your work**: Keep a record of successful examples for reference

---

## 🎯 Quick Example to Test Everything

Try this example to make sure everything works:

1. **Run**: `python cldr_converter.py`
2. **Path**: Type `yes`
3. **English**: Type `August 10, 2025`
4. **Translation**: Type `yes`
5. **Language**: Type `spanish`
6. **Spanish**: Type `10 de agosto 2025`

**Expected result**:
```
English skeleton: MMMM d, y
Spanish skeleton: d 'de' MMMM y
```

If you see this, everything is working correctly! 🎉 