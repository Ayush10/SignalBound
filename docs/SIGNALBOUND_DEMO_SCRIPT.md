# SignalBound: 90-Second Hackathon Demo Script

**Goal**: Showcase the seamless integration of high-performance C++ combat with a generative AI "System" narrative layer.

---

### **0s - 15s: The Awakening (Hub)**
*   **Action**: Start in `Map_HubCitadelCity`. Camera pans across the vibrant flora of the Grand Hall.
*   **System Event**: The HUD initializes. Mistral-generated directive appears: *"The Citadel remembers those who fall. Rise again, Signalbound."*
*   **Vocal**: ElevenLabs synthesizes the line in a cold, authoritative voice.
*   **Narration**: *"Welcome to SignalBound. You are a warrior tethered to an omnipresent System that directs your every move."*

### **15s - 30s: The Descent (Transition)**
*   **Action**: Walk to `BP_AscensionGate_00`. Trigger the transition.
*   **Visual**: Screen fades/loads into `Map_Floor01_Ironcatacomb`.
*   **Narration**: *"The System tracks your progress through brutalist dungeons, providing real-time directives based on your location."*

### **30s - 60s: Systemic Combat (Action)**
*   **Action**: Engage 5 Thralls in the first combat room.
*   **Mechanics**: Showcase Light combo -> Dodge (stamina drain) -> Heavy finisher.
*   **System Event**: Trigger a "KillCount" contract.
*   **Visual**: Niagara hit impacts and sword montages play. HUD bars react smoothly.
*   **Narration**: *"Combat is frame-accurate C++, but the stakes are generative. Complete System Contracts to earn 'Signal' and survive the gauntlet."*

### **60s - 80s: The Boss Gate (Climax)**
*   **Action**: Pull the final lever. `BP_BossGate_01` glows and opens.
*   **System Event**: Mistral generates: *"Boss entity detected. Steel yourself."*
*   **Narration**: *"Every action is analyzed. The System isn't just a UI—it's a living participant in your journey."*

### **80s - 90s: Wrap Up**
*   **Action**: Final hero pose facing the Boss Arena. 
*   **Narration**: *"High-performance gameplay meets modern cloud intelligence. This is SignalBound."*

---

### **Technical Setup for Presentation**
1.  **Ensure `system_service.py` is running** in the background.
2.  **Set `ProviderMode` to LiveStub** in `BP_SystemManager` for the best AI impact.
3.  **Use `HighResShot 2`** for the cover image before starting.
