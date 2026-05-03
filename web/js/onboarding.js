let currentIntent = "";

function goToScreen(step) {
    // Hide all
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    // Show target
    document.getElementById(`screen${step}`).classList.add('active');

    const overlay = document.getElementById('bgLayer');

    if (step === 1) {
        overlay.style.clipPath = 'inset(0% 0% 0% 0% round 0px)';
    }
    else if (step === 2) {
        // Landscape rectangle mask (Make it less wide)
        // Viewport remaining is 40vw width and 35vh height
        overlay.style.clipPath = 'inset(37.5vh 35vw 37.5vh 35vw round 32px)';
        const input = document.getElementById('nameInput');
        setTimeout(() => input.focus(), 600); // Focus smoothly 
    }
    else if (step === 3) {
        // Portrait tall mask (Make it less wide)
        // Viewport remaining is 28vw width and 60vh height
        overlay.style.clipPath = 'inset(20vh 40vw 20vh 40vw round 32px)';
    }
    else if (step === 4) {
        // Full screen grass again
        overlay.style.clipPath = 'inset(0% 0% 0% 0% round 0px)';
    }
}

// Logic for pills
document.querySelectorAll('.glass-pill').forEach(pill => {
    pill.addEventListener('click', function () {
        document.querySelectorAll('.glass-pill').forEach(p => p.classList.remove('selected'));
        this.classList.add('selected');
        currentIntent = this.innerText;
    });
});

async function finishOnboarding() {
    const name = document.getElementById('nameInput').value.trim() || "User";
    const intent = currentIntent || "General Task Management";

    // Call python backend to save profile (if Eel is loaded)
    if (window.eel) {
        await eel.set_user_profile(name, intent)();
    }

    // Animate fade out
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.6s ease';

    setTimeout(() => {
        // Redirect to dashboard
        window.location.href = "index.html";
    }, 600);
}
