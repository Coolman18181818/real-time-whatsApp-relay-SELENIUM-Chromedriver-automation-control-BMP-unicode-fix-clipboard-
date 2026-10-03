from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import traceback
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
import random
import re
import hashlib
import pyperclip

driver = webdriver.Chrome()
driver.get("https://web.whatsapp.com")
wait = WebDriverWait(driver, 90)
wait2 = WebDriverWait(driver,3)





def clean_emoji_text(text):
    """
    Handle non-BMP emojis by either:
    1. Keeping them if possible, or
    2. Replacing with text representation
    """
    if not text:
        return text
    
    
    # Method 2: Replace non-BMP emojis with text equivalents
    emoji_map = {
        # Location / Map
        '📍': '⛳',       # simple bullet
        '📌': '📌',       # pin/target
        '🗺️': '⛳',       # map-like square

        # Date / Time
        '🗓': '☑',       # calendar/task
        '📅': '☑',       # calendar/task
        '⏰': '⏰',       # alarm clock
        '⌚': '⏰',       # watch → alarm
        '🕐': '⏰',       # all clocks → single BMP-safe alarm
            
        # Money emojis
        '💰': '💎',
        '💵': '💎',
        '💶': '💎',
        '💷': '💎',
        '💴': '💎',
        '💸': '💎',
        '🤑': '💎',
        '💲': '💎',
        
        # Check/Cross emojis
        '✅': '✅',   # Check mark
        '✔️': '✔',   # Remove FE0F
        '☑️': '☑',   # Remove FE0F
        '❌': '❌',   # Cross mark
        '✖️': '✖' ,   # Remove FE0F
        
        # Warning emojis
        '⚠️': '⚠',   # Remove FE0F variation selector
        '🚨': '⚠',   # Map non-BMP police light to BMP warning
        '🔔': '✸',    # Map non-BMP bell to BMP decorative alert
        
        # Message/Contact emojis
        '📩': '✉',
        '📧': '✉',
        '📞': '☎',
        '✉️': '✉',
        '👤': '☺',
        '👥': '☻',

        # Other emojis
        '🔵': '●',
        '📝': '✎',
        '🎯': '◎',
        '💼': '▣',
        '📊': '▲',
        '🔍': '⌕',
        '📋': '▣',
        '⚡': '⚡',
        '🔥': '✹',
        '💡': '☀',
        '👉': '➜',
        '\u200B': ''  # zero-width space
    }
    
     # First pass: Replace known emojis
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)


    # Remove any remaining non-BMP characters
    safe_text = []
    safe_bmp_emoji = ['⭐', '✨', '❤️', '☀️', '☁️', '⏰', '☎️']
    for char in text:
            safe_text.append(char)
    return ''.join(safe_text)

# ===== FUNCTION TO DETECT CSS BULLETS =====



def is_likely_picture_message(text):
    """Check if the message is likely just a picture notification"""
    if not text:
        return True
    
    # Common patterns for picture/image messages in WhatsApp
    picture_patterns = [
        r'^📸',                    # Camera emoji at start
        r'^image',                  # "image" at start
        r'^photo',                  # "photo" at start
        r'picture',                  # "picture"
        r'\.(jpg|jpeg|png|gif|bmp)', # File extensions
        r'^🖼️',                    # Picture frame emoji
        r'attached',                 # "attached image"
        r'image omitted',            # Common WhatsApp text
        r'media omitted',            # Another common text
        r'^\s*$',                    # Empty or whitespace only
    ]
    
    text_lower = text.lower().strip()
    
    for pattern in picture_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    # Check if it's very short (likely just an emoji)
    if len(text) < 5 and any(ord(char) > 0x10000 for char in text):
        return True
    
    return False

def is_actual_job_message(text):
    """Check if the message looks like a real job posting"""
    if not text:
        return False
    
    # Job-related keywords
    job_keywords = [
        'wage', 'pay', 'salary', 'hour', 'location', 'date',
        'time', 'attire', 'requirement', 'condition', 'jobscope',
        'duties', 'responsibilities', 'position', 'urgent'
    ]
    
    text_lower = text.lower()
    
    # Check for job keywords
    for keyword in job_keywords:
        if keyword in text_lower:
            return True
    
    # Check for common job format (bullet points, colons, etc.)
    if ':' in text and len(text) > 20:
        return True
    
    if '•' in text or '-' in text and len(text.split('\n')) > 2:
        return True
    
    return False









# ===== FUNCTION TO DETECT CSS BULLETS =====
def detect_css_bullets(message_element):
    """
    Use JavaScript to detect which lines have CSS ::before bullets
    Returns a dictionary with line text and whether it has a bullet
    """
    try:
        # Find the message container
        message_container = message_element.find_element(
            By.XPATH, 
            "./ancestor::div[contains(@class, 'message-in') or contains(@class, 'message-out')][1]"
        )
        
        # Use JavaScript to check for CSS ::before bullets
        result = driver.execute_script("""
            const container = arguments[0];
            const lines = [];
            
            // Find all direct child divs that might be lines
            const childDivs = container.querySelectorAll('div[dir="auto"]');
            
            childDivs.forEach((div) => {
                // Check if this div has a ::before pseudo-element with content
                const style = window.getComputedStyle(div, '::before');
                const content = style.getPropertyValue('content');
                
                // WhatsApp uses content: "•" for bullets
                let hasCssBullet = false;
                if (content && (content.includes('•') || content.includes('"'))) {
                    hasCssBullet = true;
                }
                
                // Get the text content
                const text = div.innerText || div.textContent;
                
                lines.push({
                    text: text.trim(),
                    hasCssBullet: hasCssBullet,
                    html: div.outerHTML
                });
            });
            
            return lines;
        """, message_container)
        
        return result
        
    except Exception as e:
        print(f"Error detecting CSS bullets: {e}")
        return []



def extract_and_preserve_emojis(text):
    """
    Extract non-BMP emojis and replace with placeholders
    Returns: (processed_text, emoji_list)
    """
    emoji_list = []
    placeholder_counter = 0
    
    def replace_emoji(match):
        nonlocal placeholder_counter
        emoji = match.group(0)
        emoji_list.append(emoji)
        placeholder_counter += 1
        return f'\x00EMOJI{placeholder_counter}\x00'  # Unique placeholder
    
    # Match all emojis (including non-BMP)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
                                                                            #"\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map symbols
                                                                            #"\U0001F700-\U0001F77F"  # Alchemical symbols
                                                                            #"\U0001F780-\U0001F7FF"  # Geometric shapes
                                                                            #"\U0001F800-\U0001F8FF"  # Supplemental arrows
        "\U0001F900-\U0001F9FF"  # Supplemental symbols
        "\U0001FA00-\U0001FA6F"  # Chess symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and pictographs extended
        "\U00002702-\U000027B0"  # Dingbats
        
        "]+", 
        flags=re.UNICODE
    )
    
    processed_text = emoji_pattern.sub(replace_emoji, text)
    return processed_text, emoji_list

def restore_emojis(text, emoji_list):
    """
    Replace placeholders with original emojis
    """
    for i, emoji in enumerate(emoji_list, 1):
        placeholder = f'\x00EMOJI{i}\x00'
        text = text.replace(placeholder, emoji)
    return text





def debug_output(message_element):  # for def extract_message_with_formatting(message_element):
  # ========== ADD DEBUG CODE HERE ==========
        # DEBUG: Check structure of the message
    debug_output = driver.execute_script("""
        const element = arguments[0];
        const result = [];
        
        function debugNode(el, level) {
            for (let node of el.childNodes) {
                if (node.nodeType === Node.TEXT_NODE) {
                    let text = node.textContent;
                    if (text.trim() === '' && text.length > 0) {
                        result.push(' '.repeat(level) + 'EMPTY TEXT: "' + text + '" len=' + text.length);
                    } else if (text.trim()) {
                        result.push(' '.repeat(level) + 'TEXT: "' + text.trim() + '"');
                    }
                }
                else if (node.nodeType === Node.ELEMENT_NODE) {
                    result.push(' '.repeat(level) + '<' + node.tagName + ' class="' + node.className + '">');
                    debugNode(node, level + 2);
                }
            }
        }
        
        debugNode(element, 0);
        return result;
    """, message_element)
    
    print("\n🔍 DEBUG STRUCTURE:")
    for line in debug_output:
        print(line)
    print("="*50)
    # ========== END DEBUG CODE ==========

def remove_trailing_timestamp(text):
    # Removes timestamp stuck at the end of the full message
    cleaned = re.sub(
        r'\s*\d{1,2}:\d{2}\s*(AM|PM|am|pm)?\s*[✓✔✔️]*\s*$',
        '',           # replace with empty
        text.strip()
    )
    return cleaned


# ===== FUNCTION TO EXTRACT MESSAGE =====
def extract_message_with_formatting(message_element):
    """
    Extract message with FULL formatting:
    - Detects CSS ::before bullets from WhatsApp
    - Handles headers (lines with colon)
    - Handles sub-items under headers
    - Preserves original formatting
    """
    try:
        # STEP 1: Detect CSS bullets
        css_bullet_data = detect_css_bullets(message_element)
        print(f"🔍 Detected {sum(1 for item in css_bullet_data if item['hasCssBullet'])} lines with CSS bullets")
        

        debug_output(message_element) 
        
      


        # STEP 2: Get formatted text via JavaScript
        formatted_text = driver.execute_script("""
            const element = arguments[0];
            
            function getFullText(el) {
                let result = '';
                
                // Process all child nodes
                for (let node of el.childNodes) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        // Regular text
                        let text = node.textContent;
                                               
                        // SKIP TIMESTAMPS! 🕐
                        // Check if this text node contains timestamp patterns
                        if (text.match(/^\\s*\\d{1,2}:\\d{2}\\s*$/) ||           // "02:18"
                            text.match(/^\\s*\\d{1,2}:\\d{2}\\s*✔️?\\s*$/) ||    // "02:18 ✔️"
                            text.match(/^\\s*\\d{1,2}\\s*$/) ||                  // "24"
                            text.match(/^\\s*(yes|no|ok|okay|ty|thanks?)\\s*$/i) ||
                            text.match(/^\\s*\\d{1,2}:\\d{2}\\s*(AM|PM|am|pm)?\\s*[✓✔✔️]*\\s*$/)) { // "yes"
                            // Skip this text node completely!
                            continue;
                        }
                    
                        result += text;
                    } 
                                               
                    else if (node.nodeType === Node.ELEMENT_NODE) {
                        // Handle different elements
                        
                        // LINE BREAKS
                        if (node.tagName === 'BR') {
                            result += '\\n';
                        }
                                               
                        else if (node.tagName === 'DIV') {
                                               
                            const ariaLabel = node.getAttribute('aria-label') || '';
                          
                            if (ariaLabel === 'Quoted message') {
                                continue;
                            }
                            
                                               // Skip link preview / contact card
                            const hasCardImage = node.querySelector('[style*="height: 240px"]');
                            if (hasCardImage) {
                                continue;  // skips EVERYTHING inside _ahwq ✅
                            }
                                                            
                                               
                            let divText = '';
                            for (let child of node.childNodes){   //keyword: childNodes
                                divText += getFullText(child);
                            }       
                            
                            if (divText.trim() === ''){           // this one is to detect 'BLANK LINE' and add new-line when detected
                                result += '\\n';        
                            }
                            else{
                                result += '\\n' + divText;
                            }
                        }
                        else if (node.tagName === 'STRONG'){         //this one is to detect 'BOLD TEXT'
                            result += '*' + getFullText(node) + '*';
                        }
                        else if (node.tagName === 'EM'){
                            result += '_' + getFullText(node) + '_';                   
                        }
                        else if(node.tagName === 'LI'){                    // this one is for number bulletin 'LI'
                            const value = node.getAttribute('value') || '';   // '' , this empty string is for if, so if is empty then skip
                            const liText = getFullText(node)
                            if (liText.trim()){
                                result += value + '. ' + liText.trim();
                            }
                        }                 
                                                                                   

                      
                                            


                        else if(node.tagName === 'SPAN'){                     //for now is BACK UP
                            const styleAttr = node.getAttribute('style') || '';
                            const innerText = (node.innerText || node.textContent || '').trim();
                            const style = window.getComputedStyle(node);
                            const display = style.getPropertyValue('display');
                            
                            const isTimestamp = styleAttr.includes('--x-fontSize: 12px') || /^\\d{1,2}:\\d{2}\\s*(AM|PM|am|pm)?\\s*[✓✔]*$/.test(innerText);
                            
                            if(isTimestamp){                               //when detect 'TIMESTATUS' put 2 new-line then print the timestamp then after it will go to 'def remove_trailing_timestamp' then reomove it
                                result += '\\n\\n';  // your test marker ✅
                                continue;
                            }
                            
                            if(display === 'block' && result && !result.endsWith('\\n')){
                                result += '\\n';
                            }

                                                
                           
                            result += getFullText(node); //Add this LINE!
                        } 
                                                                                 
                        // EMOJIS (WhatsApp uses img tags for emojis)
                        else if (node.tagName === 'IMG' && node.alt) {
                            // Get actual emoji from alt text
                            result += node.alt;
                        }

                        else {
                            //👈 BULLET DETECTION HERE 

                            // First check if this element has a ::before bullet    
                            const style = window.getComputedStyle(node, '::before');
                            const bulletInfo = style.getPropertyValue('content')     //style.getPropertyValue will get all the specific Info that contains inside this '::before' example: content: "•";    
                                                                                    //                                                                                                      color: red;
                                                                                    // "::before" is all store inside this ('content') & bulletInfo is for us to use afterwards  

                                               
                            if(bulletInfo && (bulletInfo.includes('•') || bulletInfo.includes('"\\\\2022"'))){
                            result += '• ';     
                            
                            }
                            result += getFullText(node);
                        }
                    }
                }
                return result;
            }
            
            return getFullText(element);
        """, message_element) #this 'message_element' is argument[0]
        
        if formatted_text:
            # STEP 3: Clean non-BMP emojis
            original_text = formatted_text #new added 

            formatted_text = remove_trailing_timestamp(formatted_text)
            # Extract emojis and replace with placeholders
            preserved_text, emoji_list = extract_and_preserve_emojis(formatted_text)
            
            # Clean the preserved text (placeholders survive)
            cleaned_text = clean_emoji_text(preserved_text)
            
            # Restore original emojis
            cleaned_text = restore_emojis(cleaned_text, emoji_list)


            # STEP 4: Split into lines
            raw_lines = cleaned_text.split('\n')
            
            # STEP 5: Process each line with our detection data
            processed_lines = []
            line_index = 0
            
            for i, line in enumerate(raw_lines):
                line = line.strip()
                if not line:
                    processed_lines.append('')
                    continue
                
                # Check if this line had a CSS bullet (if we have data for it)
                has_css_bullet = False
                if line_index < len(css_bullet_data):
                    has_css_bullet = css_bullet_data[line_index]['hasCssBullet']
                
                # Check if line already has a bullet character
                has_char_bullet = line.startswith('•') or line.startswith('-')
                
                # STEP 6: Apply formatting based on line type
                
                # Case 1: Header line (has colon and is short)
                if ':' in line and len(line) < 40:
                    # Check if it's a special header (date, location, etc.)
                    special_headers = ['date', 'location', 'time', 'wage', 'pay', 'attire', 'requirement', 'condition', 'jobscope']
                    if any(word in line for word in special_headers):
                        # Make it bold with proper formatting
                        processed_lines.append(line)
                        #processed_lines.append(f"*{line}*") #I do not want cause this will add ** to word included inside the variable list "special_header" only 
                    else:
                        # Regular header, just keep as-is
                        processed_lines.append(line)
                
                # Case 2: Line has CSS bullet (detected from WhatsApp)
                elif has_css_bullet:
                    # Remove any existing bullet character and add our own
                    clean_line = line
                    if line.startswith('•') or line.startswith('-'):
                        clean_line = line[1:].strip()
                    processed_lines.append(f"• {clean_line}")
                    # Add a newline after bullet points for spacing
                    #processed_lines.append('')
                
                # Case 3: Line already has a bullet character
                elif has_char_bullet:
                    processed_lines.append(line)
                    #processed_lines.append('')
                
                # Case 4: Sub-item (indented under a header)
                elif processed_lines and ':' in processed_lines[-1] and not line.startswith('-') and not has_css_bullet:
                    # Check if this line is likely a sub-item (short, no colon)
                    if len(line) < 100:
                        processed_lines.append(f"{line}")
                    else:
                        processed_lines.append(line)
                
                # Case 5: Regular line
                else:
                    processed_lines.append(line)
                
                line_index += 1
            
            # STEP 7: Clean up extra newlines
            # Remove consecutive empty lines
            cleaned_processed = []
            prev_empty = False
            
            for line in processed_lines:
                if line == '':
                    if not prev_empty:
                        cleaned_processed.append(line)
                        prev_empty = True
                else:
                    cleaned_processed.append(line)
                    prev_empty = False
            
            # Remove trailing empty line
            if cleaned_processed and cleaned_processed[-1] == '':
                cleaned_processed.pop()
            
            final_text = '\n'.join(cleaned_processed)
            
            # STEP 8: Show results
            print(f"✅ Formatted text extracted successfully!")
            print(f"📊 Final lines: {len(cleaned_processed)}")
            
            return {
                'text': final_text,
                'raw': cleaned_text,
                'original':original_text,    # new added 
                'has_formatting': True,
                'bullet_lines': [i for i, item in enumerate(css_bullet_data) if item['hasCssBullet']]
            }
            
    except Exception as e:
        print(f"⚠️ Main method failed: {e}")
        traceback.print_exc()
    
    # Fallback method
    print("⚠️ Using fallback method (plain text)")
    return {
        'text': clean_emoji_text(message_element.text),
        'raw': clean_emoji_text(message_element.text),
        'has_formatting': False,
        'bullet_lines': []
    }































# Wait for chat list 
print("🔵 Please scan QR code if needed... ")
wait.until(EC.presence_of_element_located((By.ID, "pane-side")))
print("✅ WhatsApp Web loaded successfully!")


# ===== STEP 1: OPEN SOURCE CHAT =====
source_chat = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@title,'Device Source')]")))
source_chat.click()
time.sleep(3)  # Give more time for messages to load
print("✅ Source chat opened")


        

# ===== STEP 2: EXTRACT LATEST MESSAGE =====
print("\n🔵 Extracting latest message...")

try:
        
                                                          # Method 3: Look for any copyable text in messages

    
    copyable_text = wait.until(EC.visibility_of_all_elements_located(
        (By.XPATH,
        "//div[contains(@class, 'copyable-text')]")
    ))
    
    if copyable_text:
        latest_message_element = copyable_text[-1]
        backup_text = latest_message_element.text
        
        # CHECK FOR READ MORE BUTTON IN THIS SPECIFIC MESSAGE
        try:
            # Find the message container
            message_container = latest_message_element.find_element(
                By.XPATH, 
                "./ancestor::div[contains(@class, 'message-in') or contains(@class, 'message-out')][1]"
            )
            
            # Look for read more button within this container
            read_more_buttons = message_container.find_elements(                                      #detect read more
                By.XPATH, 
                ".//div[@role='button' and contains(@class, 'read-more-button')]"
            )
            
            if read_more_buttons:                                                                   #Success Opened Read More
                print("✅ Found 'read more' button in message, clicking it...")
                read_more = read_more_buttons[0]
                driver.execute_script("arguments[0].click();", read_more)
                time.sleep(1)  # Wait for expansion
                
                # Re-fetch the text after expansion
                updated_copyable = driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'copyable-text')]"
                )
                if updated_copyable:
                    latest_message_text = updated_copyable[-1].text
                    print('1 going formatting text: ')


                            # Save text in case element becomes stale

                    # Extract message using function
                    try:  #for read-More
                        message_data = extract_message_with_formatting(latest_message_element)
                        latest_message_text = message_data['text'] #['text] here mean , clean already 
                        latest_message_ori = message_data.get('original')
                        latest_data = message_data
                        latest_bullets = message_data.get('bullet_lines', []) 
                    except Exception as e:
                        print(f"⚠️ Formatting extraction failed: {e}")
                        print("✅ Using simple text extraction instead")
                        # Simple fallback using the saved text
                        message_data = {
                            'text': clean_emoji_text(backup_text),
                            'raw': backup_text,
                            'has_formatting': False
                        }

                

                    # Show the extracted message
                    print("\n" + "="*50)
                    print("📋 EXTRACTED MESSAGE:")
                    print("="*50)
                    print(latest_message_text)
                    print("="*50)
                    print(f"📊 Message length: {len(latest_message_text)} characters")
                    print(f"📊 Number of lines: {len(latest_message_text.split('\\n'))}")

                    # Ask user to verify
                    response = print("\n❓ Is this correct? (yes/no): Just say Yes ")
                    

                            
                   
                else:
                    print("updated_copyable no element: ")
                
            else:  # for no 'read-More'
                try: 
                    message_data = extract_message_with_formatting(latest_message_element)
                    latest_message_text = message_data['text']
                    latest_message_ori = message_data.get('original')
                    latest_data = message_data

                    latest_bullets = message_data.get('bullet_lines', []) 
                except Exception as e:
                    print(f"⚠️ Formatting extraction failed: {e}")
                    print("✅ Using simple text extraction instead")
                    # Simple fallback using the saved text
                    message_data = {
                        'text': clean_emoji_text(backup_text),
                        'raw': backup_text,
                        'has_formatting': False
                    }

                

                # Show the extracted message
                print("\n" + "="*50)
                print("📋 EXTRACTED MESSAGE:")
                print("="*50)
                print(latest_message_text)
                print("="*50)
                print(f"📊 Message length: {len(latest_message_text)} characters")
                print(f"📊 Number of lines: {len(latest_message_text.split('\\n'))}")

                # Ask user to verify
                response = print("\n❓ Is this correct? (yes/no): Just say Yes ")
                
                    
                
        except Exception as e:
            print(f"Error checking read more: {e}")
            latest_message_text = latest_message_element.text

    else:
        # Debug: Print all available elements to see structure
        print("⚠️ No messages found with standard selectors. Debugging...")
        
        # Print all divs with class names for debugging
        all_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'message')]")
        print(f"Found {len(all_divs)} message divs")
        
        # Take a screenshot to see what's happening
        driver.save_screenshot("debug_screenshot.png")
        print("📸 Screenshot saved as 'debug_screenshot.png'")
        
        # Print page source snippet for debugging
        page_source = driver.page_source[:1000]
        print(f"Page source snippet: {page_source[:200]}...")
        
        latest_message_text = "Test message - couldn't copy original"
    
except Exception as e:
    print(f"❌ Error finding message: {e}")
    latest_message_text = "Test message - couldn't copy original"
    import traceback
    traceback.print_exc()



print(f"\n📝 Message to be copied: '{driver}'")

  
"""
user_input = input("Is this correct? Press Enter to continue, or type 'retry' to try again: ")

if user_input.lower() == 'retry':
    # Try one more time with user assistance
    ##input("Please click on the message you want to copy, then press Enter...")
    
    try:
        # Try to get selected text or focused element
        selected_text = driver.execute_script("return window.getSelection().toString();")
        if selected_text:
            latest_message_text = selected_text
            print(f"✅ Copied selected text: '{latest_message_text}'")
    except:
        pass
"""





# ===== STEP 3: CLOSE SOURCE CHAT =====
try:
   
    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
    time.sleep(1)
except:
    chat_list = driver.find_element(By.ID, "pane-side")
    chat_list.click()
    time.sleep(1)

# ===== STEP 4: OPEN DESTINATION CHAT =====
destination_chat = wait.until(
    EC.element_to_be_clickable((By.XPATH, "//span[contains(@title, 'Device Destination ')]"))
)
destination_chat.click()
time.sleep(2)

# ===== STEP 5: FIND 'Destination Chat' MESSAGE BOX =====
message_box = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "footer div[contenteditable='true']"))
)

# ===== STEP 6: CLEAR MESSAGE BOX =====
message_box.click()
message_box.send_keys(Keys.CONTROL + "a")
message_box.send_keys(Keys.DELETE)
time.sleep(1)


# ===== STEP 7: SEND MESSAGE WITH LINE BREAKS =====
print("run: ")
print("\n🔵 Sending message with formatting...")




print("\n"*20 + '='*100)
#print(latest_message_ori)

input(f"Original Text: \n\n\n\n {latest_message_ori}")





# ===== STEP 7: SEND MESSAGE USING CLIPBOARD (FIXES BMP ERROR) =====
print("run: ")
print("\n🔵 Sending message with formatting...")

print("\n"*20 + '='*100)

# Use the message with original emojis (from message_data['text'])
message_to_send = latest_message_text
print(f"📝 Message to send (first 100 chars): {message_to_send[:100]}...")

# Copy entire message to clipboard
pyperclip.copy(message_to_send)
print("✅ Full message copied to clipboard")

# Clear message box
message_box.click()
message_box.send_keys(Keys.CONTROL + "a")
message_box.send_keys(Keys.DELETE)
time.sleep(0.5)

# Paste using Ctrl+V (bypasses BMP limitation)
from selenium.webdriver import ActionChains
action_chains = ActionChains(driver)
action_chains.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
time.sleep(0.5)

# Send the message
message_box.send_keys(Keys.ENTER)
print("✅ Message sent with EXACT emojis via clipboard!")

"""
lines =latest_message_text.split('\n')
print(f"📊 Sending {len(lines)} lines...")

# Debug: Show all lines including empty ones
for i, line in enumerate(lines):
    if line == '':
        print(f"   Line {i+1}: [EMPTY LINE]")
    else:
        print(f"   Line {i+1}: '{line[:50]}{'...' if len(line)>50 else ''}'")

# Send each line with proper handling for empty lines
for i, line in enumerate(lines):
    if line == '':
        # Empty line - press SHIFT+ENTER to create a blank line
        message_box.send_keys(Keys.SHIFT + Keys.ENTER)
        print(f"   Created blank line {i+1}")
    else:
        # Type the text
        message_box.send_keys(line)
        print(f"   Typed line {i+1}: {line[:50]}...")
        
        # Add line break if not last line
        if i < len(lines) - 1:
            message_box.send_keys(Keys.SHIFT + Keys.ENTER)
    
    time.sleep(0.1)  # Small delay for stability

# Send the message
time.sleep(0.5)
message_box.send_keys(Keys.ENTER)
print("✅ Message sent successfully with preserved blank lines!")
"""








 


"""
for i, line in enumerate(lines):
        # Show what's being sent
        print(f"   Line {i+1}: '{line[:30]}{'...' if len(line)>30 else ''}'")
        
        # Type the line
        message_box.send_keys(line)
        
        # Add line break if not last line
        if i < len(lines) - 1:
            message_box.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.2)
"""



 
# ===== STEP 8: FINAL ===== 




 
previous_original = message_data.get('original') #COMPARE
print(previous_original)
first_loop = True

count = 0
#last_message = latest_message_text       # store initial message
new_line = "\n"*3 + "-"*300 + "\n"*3

while True:
    new_message_detected = False  #reset to FALSE
    try: 
        while not new_message_detected:  # not FALSE = "WHILE TRUE"
#           'while not new_message_detected' = True
#              same as 
#           'while not False'                = True
            
            source_chat = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@title,'Device Source')]")))

            driver.find_element(By.TAG_NAME,'body').send_keys(Keys.ESCAPE)   #exit and go to SOURCE CHAT
            time.sleep(1)
            wait.until(EC.presence_of_element_located((By.ID,"pane-side")))
            source_chat.click()         
            time.sleep(3)
        
            try:                   # Extract again the Latest Message
                    updated_message_spans = driver.find_elements(By.XPATH,"//div[contains(@class, 'copyable-text')]")
                    
                    if updated_message_spans:
                                    latest_message_element = updated_message_spans[-1] #
                                    
                                   
                                    message_container = latest_message_element.find_element(
                                        By.XPATH, 
                                        "./ancestor::div[contains(@class, 'message-in') or contains(@class, 'message-out')][1]"
                                    )
                                    
                                    # Look for read more button within this container
                                    read_more_buttons = message_container.find_elements(
                                        By.XPATH, 
                                        ".//div[@role='button' and contains(@class, 'read-more-button')]"
                                    )
                                
                                    if read_more_buttons:
                                        print("✅ Found 'read more' button in message, clicking it...")   #every-time re-open have to open again
                                        read_more = read_more_buttons[0]
                                        driver.execute_script("arguments[0].click();", read_more)
                                        time.sleep(2)  # Wait for expansion

                                        updated_copyable = driver.find_elements(By.XPATH,"//div[contains(@class, 'copyable-text')]")

                                        latest_message_element = updated_copyable[-1] #


                                        
                                        
                                       



                                    

                                    else:
                                        pass
                                        print(f"pass: {new_line}  ")
                                            
                                

                                        
                                     
                                    if latest_message_element:
                                        
                                        
                                        message_data = extract_message_with_formatting(latest_message_element)
                                        current_text = message_data['text']        # Cleaned & ready to send 

                                    
                                        current_original  = message_data.get('original')  # For Compare ,   # Without random emojis!


                                        print(f"{new_line},current original text: \n {current_original}, {new_line}, previous original text: \n {previous_original}")

                                   
                                        
                                        
                                        if (current_original == previous_original): # detect the outer 1st loop
                                            count += 1
                                            print(f"All same as previous: {count}")
                                            time.sleep(2)
                                            continue
                                        else:

                                            print(f"\n\n\n\n\n\n different message detected: {current_text} \n\n\n\n\n")
                                            # ✅ DON'T extract again! Just use current_original you already have
                                            previous_original = current_original  # Update with current value
                                            new_message_detected = True
                                            break

                                            
                                            
                                        
                                     

                                    else:
                                        print("updated_copyable no element: ")
                                    
                                
                                    

                                    
                                 



                                         

                                          
                        

            except StaleElementReferenceException as e:
                print("DOM updated, Extracted Error: ", e)
                time.sleep(2)
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user (CTRL+C),          1    ")



    print(f"run: {new_line}")
    print("\n🔵 Sending message with formatting...")
    try:
        



        # ===== STEP 3: CLOSE SOURCE CHAT =====

   
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)



        # ===== STEP 4: OPEN DESTINATION CHAT =====
        destination_chat = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(@title, 'Device Destination ')]"))
        )
        destination_chat.click()
        time.sleep(2)

        # ===== STEP 5: FIND 'Destination Chat' MESSAGE BOX =====
        message_box = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "footer div[contenteditable='true']"))
        )

        # ===== STEP 6: CLEAR MESSAGE BOX =====
        message_box.click()
        message_box.send_keys(Keys.CONTROL + "a")
        message_box.send_keys(Keys.DELETE)
        time.sleep(1)





        




        # ★★★ JUST ADD THIS ONE LINE - Clean emojis before sending ★★★
        message_to_send = current_text
        print(f"📝 Message to send (first 100 chars): {message_to_send[:100]}...")

        # Copy entire message to clipboard
        pyperclip.copy(message_to_send)
        print("✅ Full message copied to clipboard")

        # Clear message box
        message_box.click()
        message_box.send_keys(Keys.CONTROL + "a")
        message_box.send_keys(Keys.DELETE)
        time.sleep(0.5)

        # Paste using Ctrl+V (bypasses BMP limitation)
        from selenium.webdriver import ActionChains
        action_chains = ActionChains(driver)
        action_chains.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(0.5)

        # Send the message
        message_box.send_keys(Keys.ENTER)
        print("✅ Message sent with EXACT emojis via clipboard!")
        
    except Exception:
        print(f"❌ Failed to send message")
      
    




















"""
    ##input('Successful: Press Enter to Continue!! ')
    if new_message_detected:
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(1)

        destination_chat = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@title, 'Zeit Geist')]")))

        destination_chat.click()
        time.sleep(2)



        message_box = wait2.until( EC.element_to_be_clickable((By.CSS_SELECTOR, "footer div[contenteditable='true']")))
        print("copy success")
        
        
        time.sleep(1)
        message_box.click()
        message_box.send_keys(Keys.CONTROL + "a")
        message_box.send_keys(Keys.DELETE)
        time.sleep(0.5)

                    # Method 1: Try using send_keys with proper line breaks

        print(input("run: "))
        print("\n🔵 Sending message with formatting...")
        try:
            # ★★★ JUST ADD THIS ONE LINE - Clean emojis before sending ★★★
            clean_message = clean_emoji_text(newest)
            
            lines = clean_message.split('\n')  # Use clean_message instead of latest_message_text
            print(f"📊 Sending {len(lines)} lines...")
            
            for i, line in enumerate(lines):
                # Show what's being sent
                print(f"   Line {i+1}: '{line[:30]}{'...' if len(line)>30 else ''}'")
                
                # Type the line
                message_box.send_keys(line)
                
                # Add line break if not last line
                if i < len(lines) - 1:
                    message_box.send_keys(Keys.SHIFT + Keys.ENTER)
                    time.sleep(0.2)
            
            # Send the message
            time.sleep(1)
            message_box.send_keys(Keys.ENTER)
            print("✅ Message sent successfully!")
            
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            traceback.print_exc()
            #RW4tzre    ASRDCXZ
            # Fallback
            try:
                print("⚠️ Trying fallback method...")
                clean_fallback = clean_emoji_text(newest)  # Clean here too
                message_box.send_keys(clean_fallback)
                message_box.send_keys(Keys.ENTER)
                print("✅ Fallback method worked!")
            except:
                print("❌ Fallback also failed")
""" 

















"""               
    try:
        lines = newest.split('\n')
        # Type each line with SHIFT+ENTER for line breaks
        for i, line in enumerate(lines):
            message_box.send_keys(line)
            if i < len(lines) - 1:  # Not the last line
            # Use SHIFT+ENTER for line break (doesn't send)
                message_box.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(0.2)
                                    
        message_box.send_keys(Keys.ENTER)  # Now press ENTER to send the complete message
        print("✅ Message sent as ONE complete message!")
    except Exception as e:
        print(f"❌ First method failed: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user (CTRL+C),          2     ")
"""
    





































def current_method1_and_2(current):
        # Method 1: Look for message text spans (most reliable for WhatsApp)
    message_spans = driver.find_elements(
        By.XPATH, 
        "//div[contains(@class, 'message-in') or contains(@class, 'message-out')]//span[contains(@class, 'selectable-text')]"
    )
    
    if message_spans:
        # Get the last message's text
        latest_message_element = message_spans[-1]
        backup_text = latest_message_element.text




            # Extract message using function
        try: 
            message_data = extract_message_with_formatting(latest_message_element)
            latest_message_text = message_data['text']
        except Exception as e:
            print(f"⚠️ Formatting extraction failed: {e}")
            print("✅ Using simple text extraction instead")
            # Simple fallback using the saved text
            message_data = {
                'text': clean_emoji_text(backup_text),
                'raw': backup_text,
                'has_formatting': False
            }
        latest_message_text = message_data['text']
        
        print(f"✅ Latest message found: '{latest_message_text}'")                 
        






    else:                                                         # Method 2: Try a more general approach
        all_text_elements = driver.find_elements(
            By.XPATH, 
            "//span[contains(@class, 'selectable-text')]"
        )
        
        if all_text_elements:
            latest_message_element = all_text_elements[-1]
            backup_text = latest_message_element.text

                   # Extract message using function
            try: 
                message_data = extract_message_with_formatting(latest_message_element)
                latest_message_text = message_data['text']
            except Exception as e:
                print(f"⚠️ Formatting extraction failed: {e}")
                print("✅ Using simple text extraction instead")
                # Simple fallback using the saved text
                message_data = {
                    'text': clean_emoji_text(backup_text),
                    'raw': backup_text,
                    'has_formatting': False
                }
            latest_message_text = message_data['text']
            print(f"✅ Latest message found (method 2): '{latest_message_text}'")





def old_ways_extracting_message(old):
    try:
        while True:
            source_chat = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@title,'TJ Job Group')]")))


            driver.find_element(By.TAG_NAME,'body').send_keys(Keys.ESCAPE)   #exit and go to SOURCE CHAT
            time.sleep(1)
            wait.until(EC.presence_of_element_located((By.ID,"pane-side")))
            source_chat.click()
            time.sleep(3)
            try: #Extract again the latest message
                updated_message_spans = driver.find_elements(By.XPATH,"//div[contains(@class, 'copyable-text')]")
                print( updated_message_spans[-1].text)
        
                
                if updated_message_spans: # this is 'selectable-text
                    newest = updated_message_spans[-1].text.strip()
                

                    if newest != last_message:
                        print("New message detected:", newest)
                        input("Press enter to continue: ")
                        last_message = newest
                        break
                    else:
                        print(f"No message{i__}")
                        i__ += 1
                else:
                    print(f"No Extracted Message{i_}")
                    i_ += 1
            except StaleElementReferenceException as e:
                print("DOM updated, Extracted Error: ", e)
                time.sleep(2)
    # While Loop stop here 
                print('success')

                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)

                destination_chat = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(@title, 'Zeit Geist')]")))

                destination_chat.click()
                time.sleep(2)

        

                message_box = wait2.until( EC.element_to_be_clickable((By.CSS_SELECTOR, "footer div[contenteditable='true']")))
                print("Method 2 success")
                
                
                time.sleep(1)
                message_box.click()
                message_box.send_keys(Keys.CONTROL + "a")
                message_box.send_keys(Keys.DELETE)
                time.sleep(0.5)

                            # Method 1: Try using send_keys with proper line breaks
                try:
                    lines = newest.split('\n')
                    # Type each line with SHIFT+ENTER for line breaks
                    for i, line in enumerate(lines):
                        message_box.send_keys(line)
                        if i < len(lines) - 1:  # Not the last line
                        # Use SHIFT+ENTER for line break (doesn't send)
                            message_box.send_keys(Keys.SHIFT + Keys.ENTER)
                            time.sleep(0.2)
                                                
                    message_box.send_keys(Keys.ENTER)  # Now press ENTER to send the complete message
                    print("✅ Message sent as ONE complete message!")
                except Exception as e:
                    print(f"❌ First method failed: {e}")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user (CTRL+C),          1     ")


                    
            

        #finally:
        #   input("wait.....")
        #  print("Closing browser...")
        #  driver.quit()

    """
    def AI_read_more(message_element):
    
        Check if message has read more button and click it
        
        if not message_element: # to check whether it has value , if have then run next code , if no then return FALSE
            input(f"False: "{False})
            return False
        
        try:
            # Find the message container
            message_container = message_element.find_element(
                By.XPATH, 
                "./ancestor::div[contains(@class, 'message-in') or contains(@class, 'message-out')][1]"
            )
            
            # Look for read more button
            read_more_buttons = message_container.find_elements(
                By.XPATH, 
                ".//div[@role='button' and contains(@class, 'read-more-button')]"
            )
            
            if read_more_buttons:
                read_more = read_more_buttons[0]
                driver.execute_script("arguments[0].scrollIntoView(true);", read_more)
                driver.execute_script("arguments[0].click();", read_more)
                print("✅ Clicked 'read more' button")
                
                # Wait for content to expand
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//span[contains(@class, 'selectable-text')]"))
                )
                return True
            else:
                print("ℹ️ No 'read more' button found")
                return False
                
        except Exception as e:
            print(f"❌ Error checking read more: {e}")
            return False
            """




# ===== STEP 7: SEND MESSAGE WITH LINE BREAKS =====

def old(old_ways):                                               # Method 1: Try using send_keys with proper line breaks
    try:
        # Split the message into lines
        lines = latest_message_text.split('\n')
        
        # Type each line with SHIFT+ENTER for line breaks
        for i, line in enumerate(lines):
            message_box.send_keys(line)
            if i < len(lines) - 1:  # Not the last line
                # Use SHIFT+ENTER for line break (doesn't send)
                message_box.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(0.2)
        
        time.sleep(1)
        
        # Now press ENTER to send the complete message
        message_box.send_keys(Keys.ENTER)
        
        print("✅ Message sent as ONE complete message!")
        
    except Exception as e:
        print(f"❌ First method failed: {e}")
        
                                                        # Method 2: Try using JavaScript (alternative approach)
        try:
            # Clear again
            message_box.click()
            message_box.send_keys(Keys.CONTROL + "a")
            message_box.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            # Use JavaScript to set the text with line breaks preserved
            formatted_text = latest_message_text.replace('\n', '<br>')
            
            driver.execute_script("""
                // Focus the message box
                arguments[0].focus();
                
                // Set inner HTML with <br> tags for line breaks
                arguments[0].innerHTML = arguments[1];
                
                // Trigger input event
                var event = new Event('input', { bubbles: true });
                arguments[0].dispatchEvent(event);
            """, message_box, formatted_text)
            
            time.sleep(1)
            
            # Press ENTER to send
            message_box.send_keys(Keys.ENTER)
            
            print("✅ Message sent as ONE complete message using JavaScript!")
            
        except Exception as e2:
            print(f"❌ JavaScript method also failed: {e2}")
            
                                                    # Method 3: Simple fallback
            message_box.click()
            message_box.send_keys(Keys.CONTROL + "a")
            message_box.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            message_box.send_keys(latest_message_text)
            time.sleep(0.5)
            message_box.send_keys(Keys.ENTER)
            
            print("✅ Message sent using fallback method!")

    print(f"📤 Message sent to destination chat: '{latest_message_text[:50]}...'")