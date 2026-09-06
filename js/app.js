// ===============================
// CAPITALGUARD COMMON JAVASCRIPT
// ===============================


// LOGIN

function login() {

    const username =
        document.getElementById("username").value.trim();

    const password =
        document.getElementById("password").value.trim();

    const message =
        document.getElementById("loginMessage");


    // DEMO LOGIN

    if (username === "admin" && password === "admin") {

        localStorage.setItem(
            "capitalguard_logged_in",
            "true"
        );

        window.location.href = "dashboard.html";

    } else {

        message.textContent =
            "Invalid username or password";

        message.style.color = "#d64545";

    }

}


// LOGOUT

function logout() {

    localStorage.removeItem(
        "capitalguard_logged_in"
    );

    window.location.href = "index.html";

}