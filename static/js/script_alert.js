
        const alerts = document.querySelectorAll('.alert');
        
        if (alerts.length > 0) {
            
            // Test 2: Ver si encuentra la barra de progreso
            const progressBar = alerts[0].querySelector('.alert-progress');
            
            if (progressBar) {
                progressBar.style.width = '100%';
                progressBar.style.transition = 'width 4s linear';

                setTimeout(() => {
                    alerts[0].style.opacity = '0';
                    alerts[0].style.transform = 'translateX(100%)';
                    alerts[0].style.transition = 'all 0.3s ease';
                    
                    setTimeout(() => {
                        if (alerts[0].parentNode) {
                            alerts[0].parentNode.removeChild(alerts[0]);
                        }
                    }, 300);
                }, 4000);
            } 
        }