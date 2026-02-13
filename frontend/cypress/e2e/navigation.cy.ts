describe('Navigation — Main Pages', () => {
  beforeEach(() => {
    cy.login('demo@esgadvisor.ai', 'demo1234')
  })

  it('Dashboard loads score cards and radar chart', () => {
    cy.visit('/dashboard')

    cy.contains('Tableau de Bord').should('be.visible')
    cy.contains('ENVIRONNEMENT').should('be.visible')
    cy.contains('SOCIAL').should('be.visible')
    cy.contains('GOUVERNANCE').should('be.visible')
    cy.contains('SCORE GLOBAL').should('be.visible')
    cy.contains('Radar ESG').should('be.visible')
    cy.get('canvas').should('have.length.gte', 1) // Chart.js canvases
  })

  it('Empreinte Carbone loads KPI cards', () => {
    cy.visit('/carbon')

    cy.contains('EMPREINTE TOTALE').should('be.visible')
    cy.contains('PAR EMPLOYÉ').should('be.visible')
    cy.contains('RÉPARTITION PAR SOURCE').should('be.visible')
    cy.get('canvas').should('have.length.gte', 1)
  })

  it('Score Crédit shows empty state with CTA', () => {
    cy.visit('/credit-score')

    cy.contains('Pas encore de score crédit vert').should('be.visible')
    cy.contains('Calculer mon score').should('be.visible')
  })

  it('Plan d\'Action loads progress and action items', () => {
    cy.visit('/action-plan')

    cy.contains("Plan d'amélioration ESG").should('be.visible')
    cy.contains('TOTAL ACTIONS').should('be.visible')
    cy.contains('COMPLÉTÉES').should('be.visible')
    cy.contains('Quick-wins').should('be.visible')
  })

  it('Documents shows empty state with upload CTA', () => {
    cy.visit('/documents')

    cy.contains('Documents').should('be.visible')
    cy.contains('Aucun document').should('be.visible')
    cy.contains('Uploader').should('be.visible')
  })
})
