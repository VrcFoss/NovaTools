🧰 **Nova Tools** – Blender Addon

Developed by VrcFoss (Yotva)

Compatible with: Blender **3.0+**


**Nova Tools** is a Blender addon designed to simplify the process of rigging and combining clothing with body meshes.  
It includes tools for automatic bone copying, weight transfer, scale correction, and bone cleanup.

> Available in: 🇬🇧 English | 🇫🇷 French | 🇯🇵 Japanese | 🇷🇺 Russian

---

## 🔧 Features

- **1. Setup Collections**
  - Automatically creates two collections:
    - `To_combine`: for clothing items
    - `Body`: for the character mesh and armature

- **2. Combine Clothes**
  - Transfers clothing into the Body collection
  - Copies missing bones from clothing armature to body armature
  - Applies scale correction based on reference bones (e.g., head)
  - Preserves constraints & custom properties
  - Transfers vertex weights

- **3. Auto Weight Paint (Beta)**
  - Automatically assigns weights from an armature to a selected mesh

- **4. Clean Up Bones**
  - Removes unused bones from the armature
  - Option to exclude specific bones from deletion

---

## 🛠️ Installation

1. Open **Blender**
2. Go to *Edit > Preferences > Add-ons*
3. Click *Install* and select `NovaTools.py`
4. Enable the module

---

## 📖 Usage Guide

### 1. Prepare Your Scene

- Place your **body mesh + armature** inside the `Body` collection.
- Put all **clothing meshes** in the `To_combine` collection.
- If they don't exist yet, click **"Create Default Collections"**

### 2. Combine Clothing With Body

1. Ensure clothing items are in the `To_combine` collection.
2. Click **"Combine"** under "2. Combine Clothes".
3. The plugin will:
   - Copy missing bones from clothing’s armature to body’s armature
   - Adjust clothing scale to match the body
   - Link clothing to the body’s armature
   - Move clothing to the `Body` collection and hide `To_combine`

> 💡 Tip: If your clothes already have weights or constraints, they’ll be preserved!

### 3. Auto Weight Paint (Beta)

Use this to auto-generate weights:

1. Select a mesh object
2. Choose the target armature from the dropdown
3. Click **"Generate Weights"**
4. The mesh will be parented using automatic weight painting

> ⚠️ This feature is still in beta and works best for simple cases.

### 4. Clean Up Unused Bones

1. Optionally add bones you want to keep in the **“Exclude Bones”** list
2. Click **"Remove Unused Bones"**
3. Any unused bones not excluded will be deleted

---

## 🤝 How to contribute

NovaTools is an open-source project, and all contributions are welcome! Here's how you can participate:

### 🔧 For Developers
- **Report bugs** via GitHub Issues
- **Suggest fixes** or improvements via Pull Requests
- **Add new languages** to the centralized translation system (`t(key)`)
- **Improve tests** with Blender 3.x / 4.x

### 🌍 For Translators
- Add new languages ​​to the `t(key)` function (main file)
- Translate labels, errors, tooltips, and descriptions
- Ensure existing translations are up to date

### 🎨 For UI/UX Designers
- Improve the organization of the Nova Tools panel
- Create custom icons
- Optimize usability for beginners

### 📦 For Users
- Test new versions and report bugs
- Share your workflows to inspire others Users
- Create video or written tutorials to explain features

If you want to contribute, don't hesitate to:
- Fork this repository
- Open an issue to discuss an idea or bug
- Send a pull request with your changes

Thanks in advance for your help 👏

## 💬 About

Developed by **VrcFoss (Yotva)**  
🔗 [https://vrcfoss.fr ](https://vrcfoss.fr)

🧰 [Releases](https://github.com/VrcFoss/NovaTools/releases)
    
