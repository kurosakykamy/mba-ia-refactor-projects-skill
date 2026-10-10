/** Algoritmo de Luhn — validação real de número de cartão (independente de aprovação de pagamento). */
function luhnCheck(cardNumber) {
    const digits = String(cardNumber).replace(/\D/g, '');
    if (digits.length < 12) return false;

    let sum = 0;
    let shouldDouble = false;
    for (let i = digits.length - 1; i >= 0; i--) {
        let digit = parseInt(digits[i], 10);
        if (shouldDouble) {
            digit *= 2;
            if (digit > 9) digit -= 9;
        }
        sum += digit;
        shouldDouble = !shouldDouble;
    }
    return sum % 10 === 0;
}

module.exports = { luhnCheck };
