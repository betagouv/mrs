/**
 * Ajax loading UI component. Updates the DOM to show loader
 * while request is processing. Shows error or success after
 * request is finished
 * @param {dom el} mountPoint where to insert form submission state UI
 */
export default class {
  constructor(mountPoint) {
    this.mountPoint = mountPoint
    this.document = this.mountPoint.ownerDocument

    this.overlay = this.createOverlay()
    this.hideOverlay()
  }

  /**
     * Creates overlay for form submission info
     */
  createOverlay(){
    // insert child node of overlay
    const loadingOverlay = this.document.createElement('DIV')
    loadingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            bottom: 0;
            left: 0;
            right: 0;

            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;

            background-color: rgba(0, 0, 0, 0.6);
            zIndex: 2;
            transition: opacity 0.2s linear;
            pointer-events: none;
        `
    this.mountPoint.appendChild(loadingOverlay)

    return loadingOverlay
  }

  /**
     * Shows form processing overlay
     */
  showOverlay() {
    this.overlay.style.opacity = 1
    this.overlay.style.pointerEvents = 'inherit'
  }

  /**
     * Hides form processing overlay
     */
  hideOverlay() {
    this.overlay.style.opacity = 0
    this.overlay.style.pointerEvents = 'none'
  }

  /**
     * Removes overlay content
     */
  removeOverlayContent() {
    if(this.overlay.childNodes.length) {
      this.overlay.removeChild(this.overlay.firstChild)
      this.removeOverlayContent() // remove other child node if need be
    }
  }

  /**
     * Shows UI submission loader overlay
     */
  showSubmitLoading() {
    this.removeOverlayContent()
    this.showOverlay()

    const loader = this.document.createElement('DIV')
    const loadingTextWrapper = this.document.createElement('DIV')
    const text = this.document.createTextNode('Chargement...')
    loadingTextWrapper.appendChild(text)

    loader.style.cssText = `
            height: 10vh;
            width: 10vh;
            border-radius: 50%;
            animation: rotate 1s linear;
            animation-iteration-count: infinite;
            border: 5px solid rgba(255, 255, 255, 1);
            border-left-color: rgba(0, 0, 0, 0);
        `

      loadingTextWrapper.style.marginTop = '1rem'

    this.overlay.appendChild(loader)
    this.overlay.appendChild(loadingTextWrapper)
  }

  /**
     * Shows UI form submission error message
     * @param {text} errorMsg error message to show
     */
  showSubmitError(errorMsg) {
    this.removeOverlayContent()
    this.showOverlay()

    const errorWrapper = this.document.createElement('DIV')
    const errorText = this.document.createTextNode(errorMsg)
    errorWrapper.appendChild(errorText)

    errorWrapper.style.cssText = `
            height: 2rem;
            width: 2rem;
            background-color: red;
        `

    this.overlay.appendChild(errorWrapper)
  }

  /**
     * Shows UI form submission success message
     * @param {text} successMsg success message to show
     */
  showSubmitSuccess(successMsg) {
    this.removeOverlayContent()

    const successWrapper = this.document.createElement('DIV')
    const successText = this.document.createTextNode(successMsg)
    successWrapper.appendChild(successText)

    successWrapper.style.cssText = `
            height: 2rem;
            width: 2rem;
            background-color: red;
        `

    this.overlay.appendChild(successWrapper)
  }
}
