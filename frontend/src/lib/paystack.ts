import { ApiClient } from './api'

// Paystack types
interface PaystackOptions {
  key: string
  email: string
  amount: number
  currency: string
  ref: string
  metadata: {
    user_id: string
    plan_type: string
    [key: string]: any
  }
  callback: (response: PaystackResponse) => void
  onClose: () => void
}

interface PaystackResponse {
  message: string
  reference: string
  status: string
  trans: string
  transaction: string
  trxref: string
}

declare global {
  interface Window {
    PaystackPop: {
      setup: (options: PaystackOptions) => {
        openIframe: () => void
      }
    }
  }
}

export class PaystackService {
  private static publicKey = process.env.NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY || ''

  static async loadPaystackScript(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (window.PaystackPop) {
        resolve()
        return
      }

      const script = document.createElement('script')
      script.src = 'https://js.paystack.co/v1/inline.js'
      script.async = true
      script.onload = () => resolve()
      script.onerror = () => reject(new Error('Failed to load Paystack script'))
      document.head.appendChild(script)
    })
  }

  static async initializePayment(planType: 'premium' | 'lifetime'): Promise<string> {
    try {
      const response = await ApiClient.initializePayment(planType)
      return response.payment_url
    } catch (error) {
      console.error('Error initializing payment:', error)
      throw error
    }
  }

  static async openPaymentModal(
    email: string,
    amount: number,
    planType: 'premium' | 'lifetime',
    userId: string,
    onSuccess: (reference: string) => void,
    onClose: () => void
  ): Promise<void> {
    try {
      await this.loadPaystackScript()

      const handler = window.PaystackPop.setup({
        key: this.publicKey,
        email: email,
        amount: amount * 100, // Convert to kobo/cents
        currency: 'USD',
        ref: this.generateReference(),
        metadata: {
          user_id: userId,
          plan_type: planType,
          upgrade_timestamp: new Date().toISOString()
        },
        callback: (response: PaystackResponse) => {
          if (response.status === 'success') {
            onSuccess(response.reference)
          }
        },
        onClose: onClose
      })

      handler.openIframe()
    } catch (error) {
      console.error('Error opening Paystack modal:', error)
      throw error
    }
  }

  static async verifyPayment(reference: string): Promise<any> {
    try {
      const response = await ApiClient.verifyPayment(reference)
      return response
    } catch (error) {
      console.error('Error verifying payment:', error)
      throw error
    }
  }

  private static generateReference(): string {
    const timestamp = Date.now()
    const random = Math.random().toString(36).substring(2, 15)
    return `viral_clips_${timestamp}_${random}`
  }

  static getPlanDetails(planType: 'premium' | 'lifetime') {
    const plans = {
      premium: {
        name: 'Premium Monthly',
        amount: 15,
        currency: 'USD',
        interval: 'monthly',
        description: 'Premium plan with 1080p exports, no watermark, 20 clips/day',
        features: [
          '20 viral clips per day',
          '1080p HD export quality',
          'No watermarks',
          'All aspect ratios (9:16, 1:1, 16:9)',
          'Priority processing',
          'Advanced AI detection',
          'Batch export',
          'Email support'
        ]
      },
      lifetime: {
        name: 'Lifetime Access',
        amount: 99,
        currency: 'USD',
        interval: 'one-time',
        description: 'One-time payment for lifetime access to all premium features',
        features: [
          'All Premium features',
          'Lifetime access',
          'No monthly fees',
          'Future updates included',
          'Priority support',
          'Early access to new features',
          'Commercial license',
          'Best value - Save $81/year!'
        ]
      }
    }

    return plans[planType]
  }

  static formatCurrency(amount: number, currency: string = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }
}

// React hook for Paystack integration
export const usePaystack = () => {
  const initializePayment = async (planType: 'premium' | 'lifetime') => {
    return await PaystackService.initializePayment(planType)
  }

  const openPaymentModal = async (
    email: string,
    planType: 'premium' | 'lifetime',
    userId: string,
    onSuccess: (reference: string) => void,
    onClose: () => void = () => {}
  ) => {
    const planDetails = PaystackService.getPlanDetails(planType)
    
    await PaystackService.openPaymentModal(
      email,
      planDetails.amount,
      planType,
      userId,
      onSuccess,
      onClose
    )
  }

  const verifyPayment = async (reference: string) => {
    return await PaystackService.verifyPayment(reference)
  }

  return {
    initializePayment,
    openPaymentModal,
    verifyPayment,
    getPlanDetails: PaystackService.getPlanDetails,
    formatCurrency: PaystackService.formatCurrency
  }
}
