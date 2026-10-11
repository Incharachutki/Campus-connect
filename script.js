// =========================================================
// CAMPUS CONNECT - JAVASCRIPT
// =========================================================


// =========================================================
// SEARCH EVENTS
// =========================================================

function searchEvents() {

    const input =
        document.getElementById("searchInput");

    const container =
        document.getElementById("eventContainer");

    if (!input || !container) {
        return;
    }

    const searchText =
        input.value.toLowerCase().trim();

    const eventCards =
        container.querySelectorAll(".event-card");

    eventCards.forEach(function (card) {

        const eventText =
            card.textContent.toLowerCase();

        if (eventText.includes(searchText)) {

            card.style.display = "";

        } else {

            card.style.display = "none";

        }

    });
}


// =========================================================
// OPEN REGISTRATION FOR SELECTED EVENT
// =========================================================

function openRegistration(eventName) {

    const registrationSection =
        document.getElementById("register");

    const eventSelect =
        document.getElementById("eventSelect");

    const selectedEvent =
        document.getElementById("selectedEvent");

    if (!registrationSection) {
        return;
    }

    if (eventSelect) {

        for (
            let i = 0;
            i < eventSelect.options.length;
            i++
        ) {

            if (
                eventSelect.options[i].value ===
                eventName
            ) {

                eventSelect.selectedIndex = i;
                break;
            }
        }
    }

    if (selectedEvent) {

        selectedEvent.textContent =
            "You are registering for: " +
            eventName;
    }

    registrationSection.scrollIntoView({
        behavior: "smooth"
    });
}


// =========================================================
// PAGE LOAD
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        // JavaScript initialization
        // is handled by individual functions.

    }
);