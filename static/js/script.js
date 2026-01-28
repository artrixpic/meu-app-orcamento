function calculateTotal() {
  // 1. Coleta os Custos
  const baseDaily = parseFloat(document.getElementById('base_daily_rate').value) || 0;
  const days = parseFloat(document.getElementById('labor_days').value) || 0;
  const laborCost = baseDaily * days;

  const extraCost = parseFloat(document.getElementById('extra_cost').value) || 0;

  // Soma equipamentos na lista
  let gearCost = 0;
  document.querySelectorAll('.gear-item').forEach(item => {
      gearCost += parseFloat(item.dataset.value);
  });

  const totalCost = laborCost + extraCost + gearCost;

  // 2. Coleta as Porcentagens
  const marginPercent = parseFloat(document.getElementById('margin_range').value) || 0;
  const taxPercent = parseFloat(document.getElementById('tax_input').value) || 0;

  // Atualiza Displays Visuais
  document.getElementById('display_cost').innerText = totalCost.toFixed(2);
  document.getElementById('margin_display').innerText = marginPercent;

  // 3. FÓRMULA MÁGICA (Gross Up)
  // Preço = Custo / (1 - (Margem + Imposto))

  const decimalMargin = marginPercent / 100;
  const decimalTax = taxPercent / 100;
  const divisor = 1 - (decimalMargin + decimalTax);

  let finalPrice = 0;
  const alertMsg = document.getElementById('alert_msg');

  if (divisor <= 0) {
      finalPrice = 0;
      alertMsg.innerText = "⚠️ Impossível! Margem + Imposto > 100%";
  } else {
      finalPrice = totalCost / divisor;
      alertMsg.innerText = "";
  }

  // 4. Atualiza Tela Final
  document.getElementById('final_price_display').innerText = finalPrice.toFixed(2);

  // 5. Atualiza Inputs Ocultos (para enviar ao Backend)
  document.getElementById('total_cost_input').value = totalCost;
  document.getElementById('final_price_input').value = finalPrice;
}

// Roda uma vez ao carregar
window.onload = calculateTotal;