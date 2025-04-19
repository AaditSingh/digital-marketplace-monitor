import { auth } from './firebaseConfig.js';
import { createUserWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/9.6.10/firebase-auth.js";

document.querySelector('form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm-password").value;

    if (password !== confirmPassword) {
        alert("Passwords do not match");
        return;
    }

    try {
        await createUserWithEmailAndPassword(auth, email, password);
        alert("Signup successful!");
        window.location.href = "dashboard_page.html";
    } catch (err) {
        alert("Signup failed: " + err.message);
    }
});