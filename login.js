import { auth, provider } from './firebaseConfig.js';
import {
    signInWithEmailAndPassword,
    signInWithPopup
} from "https://www.gstatic.com/firebasejs/9.6.10/firebase-auth.js";

document.querySelector('form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
        await signInWithEmailAndPassword(auth, email, password);
        alert("Login successful!");
        window.location.href = "dashboard_page.html";
    } catch (err) {
        alert("Login failed: " + err.message);
    }
});

document.getElementById("google-login").addEventListener("click", async () => {
    try {
        await signInWithPopup(auth, provider);
        alert("Google login successful!");
        window.location.href = "dashboard_page.html";
    } catch (err) {
        alert("Google login failed: " + err.message);
    }
});