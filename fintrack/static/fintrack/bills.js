// Disable recurrencePeriod dropdown if isRecurring is No
document.addEventListener("DOMContentLoaded", () => {
    const isRecurring = document.querySelector('#is_recurring');
    const recurrencePeriod = document.querySelector('#recurrence_period');

    const dropdownState = () => {
        if (isRecurring.value == "No") {
            recurrencePeriod.disabled = true;
        } else {
            recurrencePeriod.disabled = false;
        }
    };

    isRecurring.addEventListener("change", dropdownState);
    dropdownState();
});