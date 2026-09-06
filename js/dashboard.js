const allocationCanvas =
    document.getElementById("allocationChart");

if (allocationCanvas) {

    new Chart(allocationCanvas, {

        type: "doughnut",

        data: {

            labels: [
                "Equity",
                "Bonds",
                "Gold",
                "Corporate Bonds",
                "Cash"
            ],

            datasets: [{

                data: [
                    35,
                    30,
                    15,
                    10,
                    10
                ]

            }]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            plugins: {

                legend: {
                    position: "bottom"
                }

            }

        }

    });

}