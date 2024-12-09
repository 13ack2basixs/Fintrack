document.addEventListener("DOMContentLoaded", () => {
    const budgetItems = document.querySelectorAll(".budget-list li");

    budgetItems.forEach((item) => {
        const amountSpent = parseFloat(
            item.querySelector(".budget-amount-spent").textContent.replace("$", "").trim()
        );
        const totalBudget = parseFloat(
            item.querySelector(".budget-total").textContent.replace("$", "").trim()
        );

        const progressBar = item.querySelector(".progress-bar");

        if (amountSpent > totalBudget) {
            item.style.color = "red";
            progressBar.classList.add("progress-over-budget");
        } else {
            item.style.color = "black";
            progressBar.classList.remove("progress-over-budget");
        }
    });
});
